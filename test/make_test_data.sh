#!/usr/bin/env bash

mkdir -p data
cd data || return 1



cat /usr/share/dict/words | grep "^a" | sort -R | head -20 > a.txt
cat /usr/share/dict/words | grep "^b" | sort -R | head -20 > b.txt
cat /usr/share/dict/words | grep "^c" | sort -R | head -20 > c.txt
cat /usr/share/dict/words | grep "^d" | sort -R | head -20 > d.txt
cat /usr/share/dict/words | grep "^e" | sort -R | head -20 > e.txt
cat /usr/share/dict/words | grep "^f" | sort -R | head -20 > f.txt

mkdir -p 20190929
cd 20190929 || return 1

cat /usr/share/dict/words | grep "^g" | sort -R | head -20 > g.txt
cat /usr/share/dict/words | grep "^h" | sort -R | head -20 > h.txt
cat /usr/share/dict/words | grep "^i" | sort -R | head -20 > i.txt
cat /usr/share/dict/words | grep "^j" | sort -R | head -20 > j.txt
cat /usr/share/dict/words | grep "^k" | sort -R | head -20 > k.txt
cat /usr/share/dict/words | grep "^l" | sort -R | head -20 > l.txt
