# Myrror
A basic tree mirroring utility meant to detect moves and renames efficiently

## This project is a work in progress. It is not functionnal at the moment

The goal is to detect similar files on source and destination in order to copy only the strict minimum from src to dst

The detection criteria can be chosen by the user. 
They include modified date, path, name, quick hash (hash of a small fraction of the beginning, middle and end of a file)
full hash and byte-to-byte comparison. The order can be set in order to avoid computing a complete hash
if the quick hash differs.

Once the comparison is performed, files only on src are copied to dst and files on dst are moved/copied/removed as necessary
to make it an identical copy of src.

Trying to implement it myself made me understand why such solutions do not already exist: there are MANY
weird edge cases to consider and the implementation is much more complex than it seems.

I do NOT know when this project will be finished, i already restarted it from scratch twice to take in account
cases i did not think of. Plus this is a personal project and i do not have much time to dedicate to it for now
