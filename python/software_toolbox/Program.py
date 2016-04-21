import sys

sys.path.append('/usr/local/lib/scons-2.3.0')

import SCons.Node.FS
import SCons.Environment

class Program:

    def __init__(self, name, env):
        self._name = name
        self._env = env
        self._directory = env.Dir('knud')

    def getMapFile(self):
        return self._directory.File(self._name + '.map')


## example ##

testArray = []
testArray.append('element1')
testArray.append('element2')
print testArray
print map(len,testArray)

env = SCons.Environment.Environment()
env.VariantDir('knud','bin')

knudsProgram = Program('knudsProgram', env)
print knudsProgram.getMapFile().get_dir().variant_dirs


## test ##
