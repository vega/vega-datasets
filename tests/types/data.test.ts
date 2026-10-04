import data from "../../src/index.js";

const loader = data["cars.json"];
const url: string = loader.url;
const result: Promise<unknown> = loader();

// @ts-expect-error The loader URL is a string.
const invalidUrl: number = loader.url;

// @ts-expect-error The URL belongs to the loader, not its returned promise.
loader().url;

// @ts-expect-error Only registered dataset names are accepted.
data["not-a-dataset.json"];
