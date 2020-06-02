#!/usr/bin/env bash

echo "import {version} from '../package.json';"
echo 'export default {'
echo ''

for file in data/*.json data/*.csv data/*.tsv data/*.arrow; do
    name=${file##*/}
    echo "  '$name': \`https://cdn.jsdelivr.net/npm/vega-datasets@\${version}/data/$name\`,"
done

echo '}'
