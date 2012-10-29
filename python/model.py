# coding=UTF-8

import os
import subprocess

class Primitive:
    def __init__(self, text):
        self.name, self.bintype, self.cxxtype, self.javatype, self.desc = text.split('\t')
        self.comment = ''

    def check(self):
        return

    def type(self):
        type = 'simple'
        if self.bintype == 'compound':
            type = 'compound'
        if self.cxxtype == 'enum' or self.javatype == 'enum':
            type = 'enum'
        return type

class Enum:
    def __init__(self, name):
        self.name = name
        self.values = dict()

    def check(self):
# TODO: Check for duplicate names (and values).
        return

class EnumValue:
    def __init__(self, name, number, symbol, description):
        self.name = name
        self.number = number
        self.symbol = symbol
        self.desc = description
        self.comment = ''

    def check(self):
        return

class Compound:
    def __init__(self, name):
        self.name = name
        self.members = dict()

    def check(self):
# TODO: Check for duplicate names (and members).
        return

class CompoundMember:
    def __init__(self, seqno, type, name, description):
        self.seqno = seqno
        self.type = type
        self.name = name
        self.desc = description
        self.comment = ''

    def check(self):
        return

class Shape:
    def __init__(self, text):
        self.id, self.name, self.dim, self.desc = text.split('\t')
        self.inherit_in = set()
        self.inherit_out = set()
        self.rep_in = set()
        self.rep_out = set()
        self.rep_canonical = None
        self.comment = ''
        self.inherit_comment = dict()

        if (self.id != 'ShapeID'):
            self.id = int(self.id)

    def check(self):
        if (self.name not in ['Scale', 'Grid', 'Text']):

            if self.rep_canonical == None:
                raise Exception('Shape ' + str(self.id) + ' has no canonical representation')

            if self.rep_canonical not in self.rep_in:
                raise Exception('Shape ' + str(self.id) + ' does not have the canonical representation as an input representation')

            if self.rep_canonical not in self.rep_out:
                raise Exception('Shape ' + str(self.id) + ' does not have the canonical representation as an output representation')

        return

    def reps(self):
        used = set()
        reps = dict()
        self.__reps(reps, used)

        return reps

    def reps_in(self):
        used = self.rep_in
        for s in self.inherited_in():
            used |= s.rep_in
        return used

    def reps_out(self):
        used = self.rep_out
        for s in self.inherited_out():
            used |= s.rep_out
        return used

    def __reps(self, reps, used):
        for r in self.rep_in | self.rep_out:
            if (r in reps):
                reps[r].add(self)
            else:
                reps[r] = set([self])
        used.add(self)
        for s in self.inherit_in | self.inherit_out:
            if (s not in used):
                s.__reps(reps, used)
        return

    def inherited_in(self):
        used = set()
        self.__inherited_in(used)
        used.remove(self)
        return used

    def __inherited_in(self, used):
        used.add(self)
        for s in self.inherit_in:
            if (s not in used):
                used.add(s)
                s.__inherited_in(used)

    def inherited_out(self):
        used = set()
        self.__inherited_out(used)
        used.remove(self)
        return used

    def __inherited_out(self, used):
        used.add(self)
        for s in self.inherit_out:
            if (s not in used):
                used.add(s)
                s.__inherited_out(used)

    # If we inherit a shape, we can use of all its in representations.
    def has_rep_in(self, rep):
        found = 0
        if rep in self.rep_in:
            found = 1
        else:
            for s in self.inherited_in():
                if s.__has_rep_in(rep):
                    found = 2
                    break
        return found

    def __has_rep_in(self, rep):
        found = 0
        if rep in self.rep_in:
            found = 1
        return found

    # If we inherit a shape, we can't necessarily use its out
    # representations (need to look up if that's possible using its in
    # representations directly).  i.e. we check if it inherits us (in
    # reverse)
    def has_rep_out(self, rep):
        found = 0
        if rep in self.rep_out:
            found = 1
        else:
            for s in self.inherited_out():
                if self in s.inherit_out and s.__has_rep_in(rep):
                    found = 2
                    break
        return found

    def __has_rep_out(self, rep):
        found = 0
        if rep in self.rep_out:
            found = 1
        return found

class Representation:
    def __init__(self, text):
        self.id, self.name, self.dim, self.desc = text.split('\t')
        self.members = dict()
        self.comment = ''

        if (self.id != 'RepID'):
            self.id = int(self.id)

    # Consistency check.  Make sure that sequence numbers are correct,
    # with no missing numbers.
    def check(self):
        print('Checking ' + self.name + ':' + self.dim)
        for member in self.members.values():
            member.check()

        s = set()
        for member in self.members.values():
            s.add(member.seq)

        if (len(s) == 0):
            raise Exception("No members for representation " + str(self.id))

        m = max(s)
        if (s != set(range(0,m+1))):
            raise Exception("Invalid sequence IDs for representation " + str(self.id))
        return

    def dump_cxx_header(self, stream):
        name = self.name[1:] + self.dim
        print(name)

        slen = 14 + len(name) + 1
        nlen = max([len(x.name) for x in self.members.values()])
        tlen = max([len(x.type) for x in self.members.values()])
        print(nlen, '-', tlen)

        ctor=''
        members = ''
        mlist = list(self.members.keys())
        mlist.sort()
        print(mlist)
        for i in mlist:
            m = self.members[i]
            if (i > 0):
                ctor += ' ' * slen
            ctor += m.type + ' ' * (tlen - len(m.type)) + ' ' + m.name;
            if i != max(mlist):
                ctor += ',\n'

            template = """
      class {0}
      {{
         public:
              {0}({1});

              ~{0}()
              {{}}

          {2}
      }}
"""
        stream.write(template.format(name, ctor, members))

class RepresentationMember:
    def __init__(self, seq, name, type, desc):
        self.seq = seq
        self.name = name
        self.type = type
        self.desc = desc
        self.comment = ''

        self.seq = int(self.seq)

    def check(self):
        return

class Model:
    def __init__(self):
        self.primitive_names = dict()
        self.enum_names = dict()
        self.compound_names = dict()
        self.shape_ids = dict()
        self.shape_names = dict()
        self.representation_ids = dict()
        self.representation_names = dict()

        self.load_primitives()
        self.load_enums()
        self.load_compounds()
        self.load_shapes()
        self.load_reps()
        self.load_rep_members()
        self.load_shape_reps()
        self.load_shape_rels()
        self.check()

    def load_primitives(self):
        # Load shapes
        comment = ''
        for line in open ('spec/primitives.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            primitive = Primitive(line)
            if (len(comment) > 0):
                primitive.comment = comment
                comment = ''
            if primitive.name in self.primitive_names:
                raise Exception("Duplicate primitive " + primitive.name+':'+primitive.dim)
            self.primitive_names[primitive.name] = primitive

        # TODO: Sort
        for primitive in self.primitive_names.values():
            print(primitive.name)


    def load_enums(self):
        # Load shapes
        comment = ''
        for line in open ('spec/enums.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            print(line)
            primitive, name, number, symbol, desc = line.split('\t')

            enum = None
            if primitive in self.enum_names:
                enum = self.enum_names[primitive]
            else:
                enum = Enum(primitive)
                self.enum_names[primitive] = enum
                print('** Added ** ' + primitive)

            val = EnumValue(name, number, symbol, desc)
            if (len(comment) > 0):
                val.comment = comment
                comment = ''
            if val.name in enum.values:
                raise Exception("Duplicate enum " + enum.name+':'+ val.name)
            enum.values[val.name] = val

        # TODO: Sort
        for enum in self.enum_names.values():
            print(enum.name)

    def load_compounds(self):
        # Load shapes
        comment = ''
        for line in open ('spec/compounds.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            print(line)
            primitive, seqno, type, name, desc = line.split('\t')

            compound = None
            if primitive in self.compound_names:
                compound = self.compound_names[primitive]
            else:
                compound = Compound(primitive)
                self.compound_names[primitive] = compound
                print('** Added ** ' + primitive)

            mb = CompoundMember(seqno, type, name, desc)
            if (len(comment) > 0):
                mb.comment = comment
                comment = ''
            if mb.name in compound.members:
                raise Exception("Duplicate compound " + compound.name+':'+ mb.name)
            compound.members[mb.name] = mb

        # TODO: Sort
        for compound in self.compound_names.values():
            print(compound.name)


    def load_shapes(self):
        # Load shapes
        comment = ''
        for line in open ('spec/shapes.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            shape = Shape(line)
            if (len(comment) > 0):
                shape.comment = comment
                comment = ''
            if shape.id in self.shape_ids:
                raise Exception("Duplicate shape ID " + shape.id)
            self.shape_ids[shape.id] = shape
            if shape.name+':'+shape.dim in self.shape_names:
                raise Exception("Duplicate shape " + shape.name+':'+shape.dim)
            self.shape_names[shape.name+':'+shape.dim] = shape

    def load_reps(self):
        comment = ''
        # Load representations
        for line in open ('spec/representations.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            representation = Representation(line)
            if (len(comment) > 0):
                representation.comment = comment
                comment = ''
            if representation.id in self.representation_ids:
                raise Exception("Duplicate representation ID " + str(representation.id))
            self.representation_ids[representation.id] = representation
            if representation.name+':'+representation.dim in self.representation_names:
                raise Exception("Duplicate representation name+dim " + representation.name+':'+representation.dim)
            self.representation_names[representation.name+':'+representation.dim] = representation

    def load_rep_members(self):
        # Load representation members
        comment = ''
        for line in open ('spec/representationmembers.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            print(line)
            name, dim, memberseq, membername, membertype, memberdesc = line.split('\t')
            memberseq = int(memberseq)
            representation = self.representation_names[name+':'+dim]
            member = RepresentationMember(memberseq, membername, membertype, memberdesc)
            if (len(comment) > 0):
                member.comment = comment
                comment = ''
            if memberseq in representation.members:
                raise Exception("Duplicate representation " + str(representation.id) + " sequence " + str(memberseq))
            representation.members[memberseq] = member

    def load_shape_reps(self):
        # Load shape representations
        for line in open ('spec/shapereps.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0 or line[0] == '#'):
                continue
            shape, dim, rep, repdim, repin, repout, repcanonical, details = line.split('\t')
            s = self.shape_names[shape+':'+dim]
            srep = self.representation_names[rep+':'+repdim]
            if (repin == 'true'):
                s.rep_in.add(srep)
            if (repout == 'true'):
                s.rep_out.add(srep)
            if (repcanonical == 'true'):
                s.rep_canonical = srep

    def load_shape_rels(self):
        # Load shape relations
        comment = ''
        for line in open ('spec/shaperel.txt', 'rt'):
            line = line.rstrip('\n')
            if (len(line) == 0):
                continue
            if (line[0] == '#'):
                if (len(line) > 1 and line[1] == ' '):
                    comment += line[2:] + '\n'
                continue
            shape, dim, inherit, inheritdim, shapein, shapeout = line.split('\t')
            s = self.shape_names[shape+':'+dim]
            si = self.shape_names[inherit+':'+inheritdim]
            if (shapein == 'true'):
                s.inherit_in.add(si)
            if (shapeout == 'true'):
                s.inherit_out.add(si)
            if (len(comment) > 0):
                s.inherit_comment[inherit] = comment
                comment = ''

    def check(self):
        for shape in self.shape_ids.values():
            shape.check()
        for representation in self.representation_ids.values():
            representation.check()
# TODO: Add other types
# Validate that all enums and compounds have detailed form.
        return

    def prepare_gen(self):
        if not os.path.exists("gen"):
            os.makedirs("gen")

    def primitiveref(self, name, primitive):
        return ':ref:`' + name + ' <primitive_' + primitive + '>`'

    def enumref(self, name, enum):
        return ':ref:`' + name + ' <enum_' + enum + '>`'

    def compoundref(self, name, compound):
        return ':ref:`' + name + ' <compound_' + compound + '>`'

    def shaperef(self, name, shape, dim):
        return ':ref:`' + name + ' <shape_' + shape + '_' + dim + '>`'

    def repref(self, name, rep, dim):
        return ':ref:`' + name + ' <rep_' + rep + '_' + dim + '>`'

    def dump_primitivelist(self):
        self.prepare_gen()

        fr = open('primitives.rst','w')

        f = open('gen/primitives.txt','w')
        fc = open('gen/primitives-c++.txt','w')
        fj = open('gen/primitives-java.txt','w')

        header = """Fundamental data types
======================

The following defined types are used in the subsequent sections.
Implementors should treat these sizes as minimium requirements.

.. note::
    **Roger Leigh**  Depending upon how we wish to persue
    interoperability between implementations, these may be required to
    be exact.  Using plain text would mitigate this to an extent.

.. csv-table:: Primitives
    :header-rows: 1
    :file: gen/primitives.txt
    :delim: tab

.. csv-table:: C++ primitives
    :header-rows: 1
    :file: gen/primitives-c++.txt
    :delim: tab

.. csv-table:: Java primitives
    :header-rows: 1
    :file: gen/primitives-java.txt
    :delim: tab

.. note::
    **Barry DeZonia** Support different coordinate spaces as needed
    (int, long, double).  Should be possible to iterate some regions.

"""
        fr.write(header)

        f.write("Name\tBinType\tDescription\n")
        fc.write("Name\tC++ Type\n")
        fj.write("Name\tJava Type\n")
        primitives = list(self.primitive_names.keys())
        primitives.sort()
        for name in primitives:
            primitive = self.primitive_names[name]
            lname = self.primitiveref(primitive.name, primitive.name)
            if primitive.type() == 'enum':
                lname = self.enumref(primitive.name, primitive.name)
            elif primitive.type() == 'compound':
                lname = self.compoundref(primitive.name, primitive.name)
            print('test ' + primitive.name + ' is ' + primitive.type() + ' ' + lname)
            cxxtype = primitive.cxxtype
            if cxxtype == 'enum':
                cxxtype = self.enumref(primitive.name, primitive.name)
            javatype = primitive.javatype
            if javatype == 'enum':
                javatype = self.enumref(primitive.name, primitive.name)
            f.write(lname + '\t' +
                    primitive.bintype + '\t' +primitive.desc + '\n')
            fc.write(lname + '\t' + cxxtype + '\n')
            fj.write(lname + '\t' + javatype + '\n')
        f.close()
        fc.close()
        fj.close()
        fr.close()

    def dump_enums(self):
        self.prepare_gen()

        fe = open('enums.rst','w')

        header="""Enumerated types
================

"""

        fe.write(header)

        names = list(self.enum_names.keys())
        names.sort()
        for name in names:
            enum = self.enum_names[name]
            filename = 'gen/enum-' + enum.name + '.txt'

            template = """
.. index::
    {0}

.. _enum_{0}:

{0}
{1}

.. csv-table:: {0}
    :header-rows: 1
    :file: {2}
    :delim: tab

"""
            fe.write(template.format(enum.name, '^' * len(enum.name), filename))

            symbols = False
            for sym in [x.symbol for x in enum.values.values()]:
                if sym != '':
                    symbols = True
            enumtab = open(filename, 'w')
            print('Writing '+ filename)
            if (symbols):
                enumtab.write('Name\tNumber\tSymbol\tDescription\n')
            else:
                enumtab.write('Name\tNumber\tSymbol\tDescription\n')

            values = list(enum.values.values())
            values.sort(key = lambda x: x.number)

            for val in values:
                enumtab.write(val.name + '\t' + str(val.number) + '\t')
                if (symbols):
                    enumtab.write(val.symbol + '\t')
                enumtab.write(val.desc + '\n')
            enumtab.close()

        fe.close()

    def dump_compounds(self):
        self.prepare_gen()

        fe = open('compounds.rst','w')

        header="""Compound types
==============

"""

        fe.write(header)

        names = list(self.compound_names.keys())
        names.sort()
        for name in names:
            compound = self.compound_names[name]
            filename = 'gen/compound-' + compound.name + '.txt'

            template = """
.. index::
    {0}

.. _compound_{0}:

{0}
{1}

.. csv-table:: {0}
    :header-rows: 1
    :file: {2}
    :delim: tab

"""
            fe.write(template.format(compound.name, '^' * len(compound.name), filename))

            compoundtab = open(filename, 'w')
            print('Writing '+ filename)
            compoundtab.write('SeqNo\tType\tName\tDescription\n')

            members = list(compound.members.values())
            members.sort(key = lambda x: x.seqno)

            for mb in members:
                compoundtab.write(str(mb.seqno) + '\t' + mb.type + '\t' +
                                  mb.name + '\t' +mb.desc + '\n')
            compoundtab.close()

        fe.close()

    def dump_shapelist(self):
        self.prepare_gen()

        f = open('gen/shapes.txt','w')
        f.write("ID\tShape\tDims\tDescription\n")
        shapes = list(self.shape_ids.keys())
        shapes.sort()
        for id in shapes:
            shape = self.shape_ids[id]
            f.write(str(shape.id) + '\t:ref:`' + shape.name + ' <shape_' +
                    shape.name + '_' + shape.dim + '>`\t' +
                    shape.dim + '\t' + shape.desc + '\n')

    def dump_replist(self):
        self.prepare_gen()

        f = open('gen/representations.txt','w')
        f.write("ID\tRepresentation\tDims\tDescription\n")
        reps = list(self.representation_ids.keys())
        reps.sort()
        for id in reps:
            rep = self.representation_ids[id]
            f.write(str(rep.id) + '\t:ref:`' + rep.name + ' <rep_' +
                    rep.name + '_' + rep.dim + '>`\t' +
                    rep.dim + '\t' + rep.desc + '\n')

    def dump_shapereps(self):
        self.prepare_gen()

        shapes = list(self.shape_ids.keys())
        shapes.sort()
        shaperst = open('shapes.rst', 'w')
        print('Writing shapes.rst')
        header = """Shapes
======

Overview
--------

.. tabularcolumns:: |r|l|l|p{3in}|
.. csv-table:: Shapes
    :header-rows: 1
    :file: gen/shapes.txt
    :delim: tab
    :widths: 2, 5, 2, 10

Definitions
-----------

Note that in the following tables, a ‘\•’ indicates a representation
implemented *directly* by a shape, while ‘*(\•)*’ indicates a
representation implemented *indirectly* through inheriting another
shape's representations for in (or vice-versa for out).

"""
        shaperst.write(header)
        for id in shapes:
            shape = self.shape_ids[id]
            filename = 'gen/shape-' + shape.name + '-' + shape.dim + '.txt'
            shapetab = open(filename, 'w')
            print('Writing '+ filename)
            shapetab.write('Representation\tDim\tIn\tOut\tInherited from\n')
            reps = shape.reps()
            replist = list(reps.keys())
            replist.sort(key = lambda x: x.name+':'+x.dim)

            for r in replist:
                repval = reps[r]
                canonical = (r == shape.rep_canonical)
                name = r.name
                if (canonical):
                    name = '**' + name + '**'
                repins = [x.name for x in shape.rep_in]
                rin = ('', '\•', '*(\•)*')[shape.has_rep_in(r)]
                rout = ('', '\•', '*(\•)*')[shape.has_rep_out(r)]
                ishapes = [x.name + ' (' + x.dim + ')' for x in reps[r]]
                ishapes.sort()
                # Make this shape name bold
                shapename = shape.name + ' (' + shape.dim + ')'
                for i in range(len(ishapes)):
                    if (ishapes[i] == shapename):
                        ishapes[i] = '**' + ishapes[i] + '** [self]'
                inherit = ', '.join(ishapes)

                shapetab.write(self.repref(r.name, r.name, r.dim) + '\t' + r.dim + '\t' +
                               rin + '\t' + rout + '\t' + inherit + '\n')
            shapetab.close()
            
            template = """
.. index::
    {0} ({2})

.. _shape_{0}_{2}:

{0} ({2})
{1}

{3}.

{4}

.. tabularcolumns:: |l|l|c|c|p{{3in}}|
.. csv-table:: {0} representations ({2})
    :header-rows: 1
    :file: {5}
    :delim: tab
    :widths: 5, 2, 2, 2, 10

"""
            shaperst.write(template.format(shape.name, '^' * (len(shape.name) + len(shape.dim) + 3), shape.dim, shape.desc, shape.comment, filename))
            if (shape.rep_canonical):
                shaperst.write('Canonical form is ' + shape.rep_canonical.name + ' (' + shape.rep_canonical.dim + ').\n\n')

            # Sphinx definition
            clist = list(shape.inherit_comment.keys())
            clist.sort()
            for c in clist:
                comment = shape.inherit_comment[c]
                if (len(comment) > 0):
                    lines = comment.split('\n')
                    shaperst.write(c + '\n')
                    for line in lines:
                        shaperst.write('    ' + line + '\n')

        footer = """Relationships
-------------

The following figure illustrates the relationships detailed in the
above tables.  Ellipses are shapes, while representations are
rectangles.  Black arrows indicate inheritance of shape
representations, while red and blue arrows indicate the
representations possible to provide as input to and obtain as output
from a shape, respectively.

.. only:: html

    .. image:: gen/inherit.svg
        :width: 100%
	:alt: Graph of object relationships

.. only:: latex

    .. image:: gen/inherit.pdf
        :width: 100%
"""

        shaperst.write(footer)
        shaperst.close()
        return

    def dump_repmembers(self):
        self.prepare_gen()

        reps = list(self.representation_ids.keys())
        reps.sort()
        reprst = open('representations.rst', 'w')
        print('Writing representations.rst')
        header="""Shape representations
=====================

Overview
--------

.. tabularcolumns:: |r|l|l|p{3.5in}|
.. csv-table:: Representations
    :header-rows: 1
    :file: gen/representations.txt
    :delim: tab
    :widths: 2, 5, 2, 10

Definitions
-----------

"""
        reprst.write(header)
        for id in reps:
            rep = self.representation_ids[id]
            filename = 'gen/rep-' + rep.name + '-' + rep.dim + '.txt'
            mtab = open(filename, 'w')
            print('Writing ' + filename)
            mtab.write('SeqNo\tName\tType\tDescription\n')
            members = rep.members
            mlist = list(members.keys())
            mlist.sort()

            for m in mlist:
                mval = members[m]
                mtab.write(str(mval.seq) + '\t' + mval.name + '\t' + mval.type + '\t' + mval.desc + '\n')
            mtab.close()

            template = """
.. index::
    {0} ({2})

.. _rep_{0}_{2}:

{0} ({2})
{1}

{3}.

{4}

.. tabularcolumns:: |r|l|l|p{{2in}}|
.. csv-table:: {0} members ({2})
    :header-rows: 1
    :file: {5}
    :delim: tab
    :widths: 2, 2, 5, 10

"""

            reprst.write(template.format(rep.name, '^' * (len(rep.name) + len(rep.dim) + 3), rep.dim, rep.desc, rep.comment, filename))

            template = """
{0}
    {1}

"""

            # Sphinx definition
            for m in mlist:
                mval = members[m]
                if (len(mval.comment) > 0):
                    lines = mval.comment.split('\n')
                    reprst.write(mval.name + '\n')
                    for line in lines:
                        reprst.write('    ' + line + '\n')

        reprst.close()
        return

    def dump_relgraph(self):
        self.prepare_gen()

        dot = open('gen/inherit.dot', 'w')
        print('Writing gen/inherit.dot')
        dot.write('digraph inheritance {\n')
#        dot.write('\tsize="4,8";\n')
        dot.write('\tnslimit=20;\n')
 #       dot.write('\tpage="6,8";\n')
#        dot.write('\tratio=fill;\n')
 #       dot.write('\taspect=0.75;')
        dot.write('\tmargin=0;\n')
        for rep in self.representation_ids.values():
            dot.write('\t"{0} ({1})" [shape=rectangle];\n'.format(rep.name, rep.dim))
        for shape in self.shape_ids.values():
            dot.write('\t"{0} ({1})" [shape=ellipse, style=filled, fillcolor="lightblue"];\n'.format(shape.name, shape.dim))
#            for i in shape.inherit_in:
#                dot.write('\t"{0} ({1})" -> "{2} ({3})";\n'.format(i.name, i.dim, shape.name, shape.dim))
#            for i in shape.inherit_out:
#                dot.write('\t"{0} ({1})" -> "{2} ({3})";\n'.format(shape.name, shape.dim, i.name, i.dim))
            for r in shape.reps_in():
                dot.write('\t"{0} ({1})" -> "{2} ({3})" [color=red];\n'.format(r.name, r.dim, shape.name, shape.dim))
            for r in shape.reps_out():
                dot.write('\t"{0} ({1})" -> "{2} ({3})" [color=blue];\n'.format(shape.name, shape.dim, r.name, r.dim))
        dot.write('}\n')
        dot.close()
        print('Generating gen/inherit.svg')
        subprocess.call(['sh', '-c', 'ccomps -x gen/inherit.dot | dot | gvpack -g | neato -n2 -Tsvg > gen/inherit.svg'])
        print('Generating gen/inherit.pdf')
        subprocess.call(['sh', '-c', 'ccomps -x gen/inherit.dot | dot | gvpack -g | neato -n2 -Tpdf > gen/inherit.pdf'])
        return

    def dump_java(self):
        print('Generating Java reference implementation')
        if not os.path.exists("java"):
            os.makedirs("java")

    def dump_cxx(self):
        print('Generating C++ reference implementation')
        if not os.path.exists("c++"):
            os.makedirs("c++")

        header = """/*
 * #%L
 * SciJava ROI Self.
 * %%
 * Copyright (C) 2012 Open Microscopy Environment:
 *   - Board of Regents of the University of Wisconsin-Madison
 *   - Glencoe Software, Inc.
 *   - University of Dundee
 * %%
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as
 * published by the Free Software Foundation, either version 2 of the 
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public 
 * License along with this program.  If not, see
 * <http://www.gnu.org/licenses/gpl-2.0.html>.
 * #L%
 */
"""

        nstart = """
#ifndef {0}
#define {0} 1

namespace scijava {{
  namespace roi {{
"""
        nend = """  }}
}}

// {0}
"""

        reph = open('c++/representations.h', 'w')
        repc = open('c++/representations.cpp', 'w')

        print('  representations')

        reph.write(header)
        repc.write(header)
        reph.write(nstart.format('SCIJAVA_REPRESENTATIONS_H'))
        reph.write('    namespace representation {\n')
        for rep in self.representation_ids.values():
 
            rep.dump_cxx_header(reph)

        reph.write('    }\n')
        reph.write(nend.format('SCIJAVA_REPRESENTATIONS_H'))
