## `{{ resource.name }}`{% if resource.title %} {{ resource.title }}{% endif %}

{% if resource.path %}
### path
{{ resource.path }}
{% endif %}
{% if resource.description %}
### description
{{ resource.description | indent(4, False) }}
{% endif %}
{% if resource.schema %}
### schema
{{ resource.schema | filter_dict(exclude=['fields']) | dict_to_markdown(level=2) }}
{{ resource.schema.fields | tabulate() }}
{% endif %}
{% if resource.sources %}
### sources
{{ resource.sources | tabulate() }}
{% endif %}
{% if resource.licenses %}
### licenses
{{ resource.licenses | tabulate() }}
{% endif %}
