param ([string] $file_path)

Remove-Item ./blockchain/output -Recurse -ErrorAction Ignore
docker run -v ${PWD}/blockchain:/sources ethereum/solc:0.8.18 -o /sources/output --abi --bin /sources/$file_path
