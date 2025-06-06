# coding: utf-8

from __future__ import absolute_import


from lcm_engine.models.base_model_ import Model
from lcm_engine import util


class ConnectivityHealth(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    """
    allowed enum values
    """
    NONE = "none"
    LAYER3 = "layer3"
    LAYER5 = "layer5"

    def __init__(self):  # noqa: E501
        """ConnectivityHealth - a model defined in OpenAPI"""
        self.openapi_types = {}

        self.attribute_map = {}

    @classmethod
    def from_dict(cls, dikt) -> "ConnectivityHealth":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ConnectivityHealth of this ConnectivityHealth.  # noqa: E501
        :rtype: ConnectivityHealth
        """
        return util.deserialize_model(dikt, cls)
