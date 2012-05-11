from __future__ import absolute_import

#########################
## Utility functions
#########################

def getSC2Classes(dct):
    #Get only DataObject classes and ignore all other attributes to allow for
    #flexibility in object class definition.
    filter = lambda v: hasattr(v, '__bases__') and DataObject in v.__mro__
    return [value for key,value in dct.iteritems() if filter(value)]

def copyObjects(src, dst):
    #For every class my parent has, if I don't have it, create an identical
    #class for me to have. We'll replace base references later!
    myClasses = [x.__name__ for x in getSC2Classes(dst.__dict__)]
    for cls in getSC2Classes(src.__dict__):
        name = cls.__name__
        if name not in myClasses:
            setattr(dst, name, type(name, cls.__bases__, dict(cls.__dict__)))
        else:
            new_cls = getattr(dst, name)
            new_cls.code = cls.code
            copyObjects(cls, new_cls)

def pull_abilities(cls):
    #Follow the bases tree down and pull all the ability codes up with you.
    if not hasattr(cls,'abilities'):
        cls.abilities = dict()

    for base in cls.__bases__:

        #Depth First Pulling. If performance is an issue we can track
        #completed classes since this will result in a lot of redundant work.
        if DataObject in base.__mro__:
            pull_abilities(base)

        #If we've got an abilities list, update ours...carefully.
        if hasattr(base, 'abilities'):
            for code, name in base.abilities.iteritems():
                if code in cls.abilities:
                    if name != cls.abilities[code]:
                        msg = "Ability codes shouldn't duplicate: {0:X} => {1}, {2}!"
                        #raise KeyError(msg.format(code, name, cls.abilities[code]))
                    else:
                        pass #it is okay
                else:
                    cls.abilities[code] = name
        else:
            pass #Some bases are just classifiers

def apply_decorators(cls):
    for subcls in getSC2Classes(cls.__dict__):
        for decorator in getattr(subcls, 'decorators', []):
            decorator()

        apply_decorators(subcls)

def pull_subclasses( cls):
    for subcls in getSC2Classes(cls.__dict__):
        if DataObject in subcls.__mro__:
            pull_subclasses(subcls)
            for subsubcls in getSC2Classes(subcls.__dict__):
                if DataObject in subsubcls.__mro__:
                    setattr(cls, subsubcls.__name__, subsubcls)


#########################
## Meta classes!
#########################

class MetaData(type):

    def __new__(self, clsname, bases, dct):
        #The base class is the exception to the rule
        if clsname == 'BaseData':
            return type.__new__(self,clsname,bases,dct)

        #Save a list of the classes we started with. We'll need it to pull base
        #class references forward and pick up the new abilities.
        myClasses = [x.__name__ for x in getSC2Classes(dct)]

        #In order for this to work, its easier if we already have made a class
        #to get around some inconvenient dictproxy issues.
        data = type.__new__(self,clsname,bases,dct)

        #Recursively copy missing classes into my dictionary. Now I can be lazy and
        #only list objects with abilities in each dictionary.
        copyObjects(bases[0], data)

        #Now that all the objects have been filled in we should apply the decorators.
        #The decorators are wrapped up so that they don't get processed until after
        #the dependencies might have been copied up from an other dictionary.
        apply_decorators(data)

        #Pull all the nested classes up. Because some decorators alter subclasses
        #this is only safe after evaluating the decorators.
        pull_subclasses(data)

        #For all the sc2objects I have, update their base references to point
        #to my other classes. This moves the tree, not just the nodes, foward.
        #also comple the ability and type codes for mapping
        dct['types'] = dict()
        dct['abilities'] = dict()
        for cls in getSC2Classes(data.__dict__):

            #Update the base class references if possible. Otherwise use the old ones
            if cls.__name__ not in myClasses:
                new_bases = list()
                for base in cls.__bases__:
                    if hasattr(data, base.__name__):
                        new_bases.append(getattr(data, base.__name__))
                    else:
                        new_bases.append(base)
                cls.__bases__ = tuple(new_bases)

            #Pull in ability information from the newly updated base references
            #into the top level abilities dictionary for this class
            pull_abilities(cls)

            #Collect the type code if its present. Otherwise, skip its abilities
            #Every ability must be tied to specific units with codes.
            if 'code' in cls.__dict__:
                dct['types'][cls.code] = cls

                #Collect the ability codes, all classes should have an
                #abilities dictionary at this point, even if its empty.
                #Make sure to only collect valid unit abilities.
                for code, name in cls.abilities.iteritems():
                    dct['abilities'][code] = name

            else:
                pass #Some classes are just classifiers

        return type.__new__(self,clsname,bases,dct)

class MetaObject(type):
    def __new__(meta,name,bases,dct):
        dct['name']=name
        if not 'abilities' in dct:
            dct['abilities'] = dict()

        for base in bases:
            if 'abilties' in base.__dict__:
                for code, name in base.abilities.iteritems():
                    dct['abilities'][code] = name
            if not 'code' in dct and 'code' in base.__dict__:
                dct['code'] = base.code

        return type.__new__(meta,name,bases,dct)

#All data is either an object or an ability
class DataObject(object):
    __metaclass__ = MetaObject
    def __init__(self, id):
        self.id = id

    def visit(self,frame,player,object_type=None):
        pass

    def __str__(self):
        return "{0} [{1:0>8X}]".format(self.__class__.__name__,self.id)

######################
## Decorators
######################

def Wrapped(func):
    def _wrapper(*args, **kwargs):
        def get_class(cls):
            if not hasattr(cls,'decorators'):
                cls.decorators = list()

            if not hasattr(cls,'abilities'):
                cls.abilities = dict()

            cls.decorators.append(lambda: func(cls, *args, **kwargs))
            return cls

        return get_class
    return _wrapper

@Wrapped
def Cloaks(cls, cloak, decloak):
    if not hasattr(cls, 'abilities'):
        cls.__dict__['abilities'] = dict()

    cls.abilities[cloak] = 'Cloak'
    cls.abilities[decloak] = 'Decloak'

@Wrapped
def Channels(cls, ability, start, cancel):
    """
    A Channel is an ability that can be canceled
    """
    if not hasattr(cls, 'abilities'):
        cls.__dict__['abilities'] = dict()

    cls.abilities[start] = ability
    cls.abilities[cancel] = "Cancel "+ability

@Wrapped
def Mode(cls, target_name, on, off):
    #some modes are not instant and the switch can be cancelled part way.
    on_name, on_code, on_cancel = on
    off_name, off_code, off_cancel = off

    target = getattr(cls,target_name)
    target.__name__ = "{0} ({1})".format(cls.__name__, target.__name__)
    if not hasattr(target, 'abilities'):
        target.abilities = dict()

    if not hasattr(cls, 'abilities'):
        cls.abilities = dict()

    cls.abilities[on_code] = on_name
    cls.abilities[on_cancel] = 'Cancel {0}'.format(on_name)
    target.abilities[off_code] = off_name
    target.abilities[off_cancel] = 'Cancel {0}'.format(off_name)

    #It seems like we need to actually cross list the mode
    #abilities. Maybe spamming screwed up the event listing?
    #Found a Sieged tank that had the "Seiege" ability used
    #while already seiged.
    #test_replays/1.2.2.17811/1.SC2REplay, player 2 - 9:40
    cls.abilities[off_code] = off_name
    cls.abilities[off_cancel] = 'Cancel {0}'.format(off_name)
    target.abilities[on_code] = on_name
    target.abilities[on_cancel] = 'Cancel {0}'.format(on_name)


def Lifts(liftoff, land):
    return Mode('Flying', ('Lift off', liftoff, None), ('Land', land, None))

def Burrows(burrow, unburrow):
    return Mode('Burrowed', ('Burrow',burrow,None), ('Unburrow',unburrow,None))

def Lowers(lower, raise_):
    return Mode('Lowered', ('Lower Supply Depot',lower,None), ('Raise Supply Depot',raise_,None))

def Uproots(uproot, root, cancel):
    return Mode('Uprooted',('Uproot',uproot,None),('Root',root,cancel))

@Wrapped
def UpgradeFrom(cls, target, start, cancel):
    target.abilities[start] = 'Upgrade to {0}'.format(target.__name__)
    target.abilities[cancel] = 'Cancel upgrade to {0}'.format(target.__name__)

@Wrapped
def Transports(cls, all_code, all_moving_code, unload_unit_code, load_unit_code):
    if all_code:
        cls.abilities[all_code] = 'Unload All'
    if all_moving_code:
        cls.abilities[all_moving_code] = 'Unload All (while moving)'
    if unload_unit_code:
        cls.abilities[unload_unit_code] = 'Unload Unit'
    if load_unit_code:
        cls.abilities[load_unit_code] = 'Load Unit'

@Wrapped
def AddOn(cls, target, start, move, cancel):
    if isinstance(target, DataObject):
        target = target.__name__

    cls.abilities[start] = 'Construct '+target
    cls.abilities[move] = 'Construct {0} (move first)'.format(target)
    cls.abilities[cancel] = 'Cancel '+target

    if hasattr(cls, target):
        getattr(cls,target).__name__ += ' ({0})'.format(cls.__name__)

@Wrapped
def MergeFrom(cls, sources, start, cancel):
    for source in sources:
        if not hasattr(source,'abilities'): source.abilities = dict()
        source.abilities[start] = 'Merge into {0}'.format(cls.__name__)
        source.abilities[cancel] = 'Cancel Merge'

@Wrapped
def MorphedFrom(cls, source, start, cancel):
    cocoon = cls.Cocoon
    cocoon.__name__ = cls.__name__+'Cocoon'

    if not hasattr(source, 'abilities'): source.abilities = dict()
    if not hasattr(cocoon, 'abilities'): cls.Cocoon.abilities = dict()

    source.abilities[start] = 'Morph to {0}'.format(cls.__name__)
    cocoon.abilities[cancel] = 'Cancel Morph to {0}'.format(cls.__name__)
