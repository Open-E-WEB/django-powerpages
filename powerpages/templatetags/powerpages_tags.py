# -*- coding: utf-8 -*-

from django import template
from django.template.base import kwarg_re
from django.utils.encoding import smart_str

from powerpages.reverse import reverse_url


register = template.Library()


def page_url_compiler(node_class):
    """
    Creates compile function for page_url* tag family
    {% tag_name alias_or_name value1 value2 kwarg1=value3 kwarg2=value4 %}
    """

    def _page_url_parser(parser, token):
        """
        Inserts page URL for given alias.
        If Page instance with given alias is not found in the CMS,
        tag acts like a standard Django {% url %} tag.
        """

        bits = token.split_contents()
        if len(bits) < 2:
            raise template.TemplateSyntaxError(
                "'%s' takes at least one argument (path to a view)" % bits[0]
            )
        name = bits[1]
        args = []
        kwargs = {}
        as_var = None
        bits = bits[2:]

        # handling "as" functionality
        if len(bits) >= 2 and bits[-2] == 'as':
            as_var = bits[-1]
            bits = bits[:-2]

        # processing bits as template vars
        if len(bits):
            for bit in bits:
                match = kwarg_re.match(bit)
                if not match:
                    raise template.TemplateSyntaxError(
                        "Malformed arguments to url tag"
                    )
                arg_name, arg_value = match.groups()
                if arg_name:
                    kwargs[arg_name] = parser.compile_filter(arg_value)
                else:
                    args.append(parser.compile_filter(arg_value))

        return node_class(name, args, kwargs, as_var)

    return _page_url_parser


class PageURLNode(template.Node):
    """
    Template tag for inserting URL leading to CMS Page or static URL.
    """

    def __init__(self, name, args, kwargs, as_var):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.as_var = as_var

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        name = self.name
        url = self.get_url(name, *args, **kwargs)

        if self.as_var:
            context[self.as_var] = url
            return ''
        else:
            return url

    def get_url(self, name, *args, **kwargs):
        """URL generation"""
        return reverse_url(name, *args, **kwargs)


page_url = register.tag(
    'page_url', page_url_compiler(PageURLNode)
)
