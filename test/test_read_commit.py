import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from utils.files import read_commit

read_commit("../data/single.txt")
read_commit("../data/multi.txt")
read_commit("../data/new_feature.txt")
