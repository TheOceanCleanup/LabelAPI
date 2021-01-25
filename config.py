from prometheus_client import Counter, Gauge, Histogram, multiprocess, CollectorRegistry
from sqlalchemy import create_engine
import os

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

number_of_labeled_images            = Counter("number_of_labeled_images", "Number of labeled images",
                                              registry=registry)
number_of_bounding_boxes_per_image  = Histogram("number_of_bounding_boxes_per_image",
                                                "Number of bounding boxes per image",
                                                registry=registry)
number_of_available_images          = Counter("number_of_available_images", "Number of available images",
                                              registry=registry)
number_of_unlabeled_images          = Gauge("number_of_unlabeled_images", "Number of unlabeled images",
                                            multiprocess_mode='livesum',
                                            registry=registry)
total_storage_container_size        = Counter("total_storage_container_size", "Total size of the storage container",
                                              registry=registry)

schema = os.environ["DB_SCHEMA"]
try:
    cur_engine = create_engine(os.environ['DB_CONNECTION_STRING'])
    with cur_engine.connect() as conn:
        labeled_images_result = conn.execute(f"""SELECT count(*) 
                                                 FROM {schema}.campaign_image 
                                                 WHERE labeled = True""")
        labeled_images = [dict(row) for row in labeled_images_result]
        number_of_labeled_images.inc(labeled_images[0]['count'])
        print(f"Number of labeled images: {labeled_images[0]['count']}")

        bounding_boxes_per_images_result = conn.execute(f"""SELECT campaign_image_id, count(*) 
                                                            FROM {schema}.object 
                                                            GROUP BY campaign_image_id""")
        bounding_boxes_per_images = [dict(row) for row in bounding_boxes_per_images_result]
        for bounding_boxes_per_image in bounding_boxes_per_images:
            number_of_bounding_boxes_per_image.observe(bounding_boxes_per_image['count'])
        print(f"Number of campaigns labeled images: {len(bounding_boxes_per_images)}")
        print(f"Number of bounding boxes: {sum([row['count'] for row in bounding_boxes_per_images])}")

        available_images_result = conn.execute(f"""SELECT count(*) 
                                                   FROM {schema}.image""")
        available_images = [dict(row) for row in available_images_result]
        number_of_available_images.inc(available_images[0]['count'])
        print(f"Number of available images: {available_images[0]['count']}")

        unlabeled_images_result = conn.execute(f"""SELECT count(*) 
                                                   FROM {schema}.campaign_image 
                                                   WHERE labeled = False""")
        unlabeled_images = [dict(row) for row in unlabeled_images_result]
        number_of_unlabeled_images.inc(unlabeled_images[0]['count'])
        print(f"Number of unlabeled images: {unlabeled_images[0]['count']}")

        storage_size_result = conn.execute(f"""SELECT sum(filesize)
                                               FROM {schema}.image""")
        storage_size = [dict(row) for row in storage_size_result]
        if storage_size[0]['sum'] is not None:
            total_storage_container_size.inc(storage_size[0]['sum'])
            print(f"Total storage size: {storage_size[0]['sum']}")
except Exception as e:
    print(f"Connect to database failed: {e}")


def worker_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
