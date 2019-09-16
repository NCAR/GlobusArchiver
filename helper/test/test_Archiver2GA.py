
import sys
import os

#sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),'configmaster'))
#print(__file__)
#print(os.path.abspath(".."))
sys.path.append(os.path.abspath(".."))

import Archiver2GA

def test_subDateStrings():
    assert Archiver2GA.subDateStrings("XXX") == "XXX"
    assert Archiver2GA.subDateStrings("DATEYYYY") == "%Y"
    assert Archiver2GA.subDateStrings("test/DATEYYYYDATEMMDD") == "test/%Y%m%d"
