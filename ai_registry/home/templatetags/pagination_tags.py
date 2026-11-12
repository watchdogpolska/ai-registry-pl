from django import template

register = template.Library()


@register.simple_tag
def query_string_replace(request, **kwargs):
    copied_get = request.GET.copy()
    for k, v in kwargs.items():
        if v is None and k in copied_get:
            del copied_get[k]
        else:
            copied_get[k] = v
    return copied_get.urlencode()


@register.simple_tag
def query_string_remove_comma_entry(request, **kwargs):
    copied_get = request.GET.copy()
    for k, v in kwargs.items():
        if k in copied_get:
            entries = copied_get[k].split(",")
            entries = [entry for entry in entries if entry != v]
            if entries:
                copied_get[k] = ",".join(entries)
            else:
                del copied_get[k]
    copied_get["page"] = 1
    return copied_get.urlencode()


@register.simple_tag
def query_string_add_comma_entry(request, **kwargs):
    copied_get = request.GET.copy()
    for k, v in kwargs.items():
        if k in copied_get:
            entries = copied_get[k].split(",")
            entries = [entry for entry in entries if entry]
            if v not in entries:
                entries.append(v)
            copied_get[k] = ",".join(entries)
        else:
            copied_get[k] = v
    copied_get["page"] = 1
    return copied_get.urlencode()
