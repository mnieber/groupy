Cache the parse result of each module when building the call graph. Groupy rebuilds the call graph from scratch
before each chunk. If parsing turns out to be too slow, Groupy can cache the parse result of each module (keyed on a
hash of its contents) inside the build. This does not change how the call graph is used.
