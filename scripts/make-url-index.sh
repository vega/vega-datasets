#!/usr/bin/env bash

echo 'export default {'

for file in data/*.json data/*.csv data/*.tsv data/*.arrow; do
    name=${file##*/}
    echo "  '$name': 'https://vega.github.io/vega-datasets/data/$name',"
done

echo '}'