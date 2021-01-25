from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, multiprocess

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
