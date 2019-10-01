[![Build Status][build-badge]][build-link]
[![Coverage Status][cov-badge]][cov-link]
[![License: MIT][mit-badge]][mit-license]
# What is this?
id3vx parses ID3 Tags of version 2.x (actually, only 2.3 for now). It can mostly dump them.

# But why?
For fun. Implementing a standard like ID3v2.x often results in a procedural, C-like hellscape
that is hard to test, extend, or even comprehend. I wanted to implement the standard using objects, kind of 
following some principles from [Elegant Objects][elegant-objects] by [Yegor Bugayenko][yegor-bugayenko] 
(check him out, his approach to OOP is awesome). I tried to write small methods (max. 10 lines) and have class names
that closely map to the specification, following the model presented in 
[Concise and consistent naming][concise-consistent] by Deissenbock and Pizka.  

# Should I use this in production?
No, please don't. If you need a serious library, check out [eyeD3][eyed3], they are doing a great job in implementing
all the tiny details that I left out ;-).

# Run
```
$ ./id3vx.py <some-file>
```

# Examples
The example files are all modifications of [this file][example-file] taken from 
[https://file-examples.com/][file-examples] which offers sample files without any copyright restrictions (thanks!).

The modifications were being done with [kid3][kid3], [easytag][easytag], and [picard][picard] to reflect the way
common tools write ID3v2.x tags.  

[build-badge]: https://travis-ci.org/suspectpart/id3vx.svg?branch=master
[build-link]: https://travis-ci.org/suspectpart/id3vx
[cov-badge]: https://coveralls.io/repos/github/suspectpart/id3vx/badge.svg?branch=master
[cov-link]: https://coveralls.io/github/suspectpart/id3vx?branch=master
[mit-badge]: https://img.shields.io/badge/License-MIT-yellow.svg
[mit-license]: https://opensource.org/licenses/MIT
[eyed3]: https://eyed3.readthedocs.io/en/latest/
[elegant-objects]: https://www.yegor256.com/elegant-objects.html
[yegor-bugayenko]: https://www.yegor256.com/
[concise-consistent]: https://ieeexplore.ieee.org/document/1421019
[example-file]: https://file-examples.com/wp-content/uploads/2017/11/file_example_MP3_700KB.mp3
[file-examples]: https://file-examples.com/
[picard]: https://picard.musicbrainz.org/
[kid3]: https://kid3.sourceforge.io/
[easytag]: https://github.com/GNOME/easytag 
