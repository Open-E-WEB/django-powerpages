# -*- coding: utf-8 -*-

from .website_base import BaseDumpLoadCommand
from powerpages.sync import WebsiteLoadOperation


class Command(BaseDumpLoadCommand):
    """LOADS website Pages FROM structure of directories and file"""

    operation_class = WebsiteLoadOperation
