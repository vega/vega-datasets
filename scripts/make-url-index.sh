#!/usr/bin/env bash

echo "import pkg from '../package.json';"
echo "const version = pkg.version;"
echo 'export default {'
echo ''

for file in data/*.json data/*.csv data/*.tsv data/*.arrow data/*.parquet; do
    name=${file##*/}
    echo "  '$name': \`https://cdn.jsdelivr.net/npm/vega-datasets@\${version}/data/$name\`,"
done

echo '}'
