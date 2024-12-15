# {{ package.name }}
`{{ package.version }}` | [GitHub]({{ package.homepage }}) | {{ package.created  | fmt_date()}}

{{ package.description }}

## licenses
{{ package.licenses | tabulate() }}

## contributors
{{ package.contributors | tabulate() }}

# resources
{% for resource in package.resources %}
  {% include 'resource-table.md' %}
{% endfor %}