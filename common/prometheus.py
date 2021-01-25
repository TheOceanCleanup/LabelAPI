from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, multiprocess

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

number_of_labeled_images            = Counter("label_storage_number_of_labeled_images",
                                              "Number of labeled images in the label storage",
                                              registry=registry)
number_of_bounding_boxes_per_image  = Histogram("label_storage_number_of_bounding_boxes_per_image",
                                                "Number of bounding boxes per image in the label storage",
                                                registry=registry)
number_of_available_images          = Counter("label_storage_number_of_available_images",
                                              "Number of available images in the label storage",
                                              registry=registry)
number_of_unlabeled_images          = Gauge("label_storage_number_of_unlabeled_images",
                                            "Number of unlabeled images in the label storage",
                                            multiprocess_mode='livesum',
                                            registry=registry)
total_storage_container_size        = Counter("label_storage_total_storage_container_size",
                                              "Total size of the storage container in the label storage",
                                              registry=registry)
