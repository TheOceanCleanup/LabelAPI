# Required details
```
api_url = "http://localhost:8080/api/v1"

admin = {
    "Authentication-Key": "KEY",
    "Authentication-Secret": "SECRET"
}

```

# Create imageset

First we create a new image set.

```
body = {
    "title": "imageset-22-10-2020",
    "metadata": {
        "country": "Nederland"
    }
}

r = requests.post(
    f"{api_url}/image_sets",
    data=body,
    headers=headers
)
print(r.json())

image_set_id = r.json()["imageset_id"]

```

# Upload images

Use `dropbox_url` in response of previous request to upload images through
(for example) storage explorer.

# Finish the image set

Now that the images are uploaded, we can finish the imageset to make it
available in the system.

```
body = {
    "new_status": "finished"
}

r = requests.put(
    f"{api_url}/image_sets/{image_set_id}",
    data=body,
    headers=headers
)
print(r.json())
```

Response will be "ok". In the background, the images are copied to their
"final" storage location, and added to the database.

# Create a labeling campaign

Lets create a labeling campaign.

```
body = {
    "title": "campaign-22-10-2020",
    "metadata": {
        "to_be_used_for": "New train set"
    },
    "labeler_email": "user@example.com"
}

r = requests.post(
    f"{api_url}/campaigns",
    data=body,
    headers=headers
)
print(r.json())

campaign_id = r.json()["campaign_id"]

user_headers = {
    "Authentication-Key": r.json()["access_token]["apikey"],
    "Authentication-Secret": r.json()["access_token]["apikey"]
}

```

The API key generated here can be shared with the labeling partner. This will
only give access to the operations on a campaign, and on reading an image. It
will not allow access to any other operations. If this user already existed in
the system (based on the email), no API secret will be returned as this is
stored in hashed form, so we don't know it.

# Add images to the campaign

Lets find all the images in the system first.

```
r = requests.get(
    f"{api_url}/images/",
    headers=headers
)
print(r.json())
```

This shows there are 4 images in the system. This request supports pagination
as it might return a lot of images. It is also possible to list the images in
a single image set using `/image_sets/{image_set_id}/images`.

Now we want to add these images to the created campaign:

```
body = [
    {"id": 1},
    {"id": 2},
    {"id": 3},
    {"id": 4}
]

r = requests.post(
    f"{api_url}/campaign/{campaign_id}/images",
    data=body,
    headers=headers
)
print(r.json())
```

We can now see the campaign, and see that 0 out of 4 images have been labeled:

```
r = requests.get(
    f"{api_url}/campaign/{campaign_id}",
    data=body,
    headers=headers
)
print(r.json())
```

# Change the status of the campaign to active

We need to indicate the campaign is ready for labeling:

```
body = {
    "new_status": "active"
}

r = requests.put(
    f"{api_url}/campaign/{campaign_id}",
    data=body,
    headers=headers
)
print(r.json())
```

# Labeling process

## Access to the images

Now the labeling partner can perform it's labeling, and share the results with
us. Note that this is done using the keys generated when creating the campaign.

They will first get a list of all images in the campaign:

```
r = requests.get(
    f"{api_url}/campaign/{campaign_id}/images",
    headers=headers
)
print(r.json())
```

This list for every image a `url`. This is relative to the base url of the API.

To retrieve an image, the labeling partner can do a normal GET request to
`<api>/images/<image_id>`. This will redirect, with a SAS token, to the actual
image.

## Providing labels

Lets first add objects for two of the images:

```
body = [
    {
        "image_id": 1,
        "objects": [
            {
                "label": "Plastic",
                "confidence": 1,
                "bounding_box": {
                    "xmin": 13,
                    "xmax": 57,
                    "ymin": 123,
                    "ymax": 198
                }
            },
            {
                "label": "Organic",
                "confidence": 0.56,
                "bounding_box": {
                    "xmin": 26,
                    "xmax": 98,
                    "ymin": 12,
                    "ymax": 54
                }
            }
        ]
    },
    {
        "image_id": 2,
        "objects": [
            {
                "label": "Wood",
                "confidence": 0.12,
                "bounding_box": {
                    "xmin": 74,
                    "xmax": 172,
                    "ymin": 91,
                    "ymax": 112
                }
            },
            {
                "label": "Plastic",
                "confidence": 0.93,
                "bounding_box": {
                    "xmin": 58,
                    "xmax": 124,
                    "ymin": 68,
                    "ymax": 98
                }
            }
        ]
    }
]

r = requests.put(
    f"{api_url}/campaign/{campaign_id}/objects" + ,
    data=body,
    headers=headers
)
print(r.json())
```

If any objects already existed for a provided image, they will be overwritten.
This allows the labeling partner to redo their labeling if required.

As asdmin, lets check the progress:

```
r = requests.get(
    f"{api_url}/campaign/{campaign_id}",
    data=body,
    headers=headers
)
print(r.json())
```

This shows that 2 out of 4 images have been labeled.

Now the labeling partner labels the other two images as well:

```
body = [
    {
        "image_id": 3,
        "objects": [
            {
                "label": "Plastic",
                "confidence": 0.433,
                "bounding_box": {
                    "xmin": 83,
                    "xmax": 153,
                    "ymin": 91,
                    "ymax": 145
                }
            }
        ]
    },
    {
        "image_id": 4,
        "objects": []
    }
]

r = requests.put(
    f"{api_url}/campaign/{campaign_id}/objects" + ,
    data=body,
    headers=headers
)
print(r.json())
```

If we now check the campaign once more, we can see 4 out of 4 images have been
labeled, and the campaign status is automatically set to "completed".

---
**NOTE**
If the labeling partner wants to override labels after this, the campaign must
first be 'reopened' by changing the status to `active`.
---

# Finishing the campaign and exporting the labels

Now all that's left to do is to finish the campaign. This is done by changing
the status to `finished`. The system will then:
- Create a Dataset in Azure ML containing the linked images, named
  `<campaign_title>_images`
- Create a CSV with the labels in Blob storage under the main upload container,
  in a folder called `label_sets`. The file will be called
  `<campaign_title>_labels.csv`.
- Create a Dataset in Azure ML containing these labels, named
  `<campaign_title>_labels`.

To start this, perform the status change:

```
body = {
    "new_status": "finished"
}

r = requests.put(
    f"{api_url}/campaign/{campaign_id}",
    data=body,
    headers=headers
)
print(r.json())
```