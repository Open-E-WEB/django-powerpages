# -*- coding: utf-8 -*-

from .website_base import BaseDumpLoadCommand
from powerpages.sync import WebsiteDumpOperation


class Command(BaseDumpLoadCommand):
    """DUMPS website Pages TO structure of directories and file"""

    operation_class = WebsiteDumpOperation
