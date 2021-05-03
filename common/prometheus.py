# LabelAPI - Server program that provides API to manage training sets for machine learning image recognition models
# Copyright (C) 2020-2021 The Ocean Cleanup™
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
