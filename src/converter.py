from parser import StringConstants, FieldDeclaration
from collections import OrderedDict
from util import *

class HeimerFormat:
    def __init__( self, objectModel ):
        self._model = objectModel
        self._userClasses = OrderedDict()
        # The class names are stored twice because we want to perserve the ordering of the classes
        self._userClassNames = list()
        # Make sure the user defined classes are of the correct format, else raise error.
        for c in self._model.classes:
            _assertValidName( c.name, self._userClasses )
            _assertValidClass( c, self._userClasses )
            self._userClasses[c.name] = c
            self._userClassNames.append(c.name)
        self._classes = OrderedDict()
        for className in self._userClasses:
            self._classes[className] = FormatField( FieldDeclaration( "N/A", className ), self._userClasses ).lines()
        self._body = FormatField( self._model.body, self._userClasses )

    def lineDelimiter(self):
        return self._model.lineDelimiter

    def commandLineOptions(self):
        return self._model.commandLineOptions

    def classes(self):
        return self._classes

    def classFormats(self):
        """ Return a list of tuples, where the tuple contains the class name and a dictionary with
        key-value pair of field name and field type (in string). """
        classes = []
        for className in self._userClassNames:
            c = self._userClasses[className]
            fields = OrderedDict()
            for line in c.lines:
                for field in line:
                    fields[field.name] = field.typeName
            classes.append( ( className, fields ) )
        return classes

    def body(self):
        return self._body


class FormatField:
    def __init__( self, field, userClasses, parent=None ):
        self._field = field
        self._userClasses = userClasses
        self._parent = parent
        _assertValidType( field.typeName, userClasses )
        self._class = None if self.isPrimitive() else userClasses[field.typeName]
        self._lines = []
        self._variables = dict()
        # If it is a user defined class, recursively construct FormatField from the variables
        # contained in the class.
        if self._class:
            for line in self._class.lines:
                fields = []
                for var in line:
                    _assertValidName( var.name, self._variables.keys() + userClasses.keys() )
                    obj = FormatField( var, userClasses, parent=self )
                    self._variables[var.name] = obj
                    fields.append(obj)
                    # Make sure if the variable has a instance repetition mode, it is either an
                    # integer, a special symbol, or an integer variable already defined in this
                    # particular user class.
                    mode = obj.instanceRepetitionModeString()
                    if ( mode and type(mode) != int and \
                        mode != StringConstants.LINE_ONE_OR_MORE and \
                        mode != StringConstants.LINE_ZERO_OR_MORE and \
                        ( mode not in self._variables or \
                        not self._variables[mode].isInteger() ) ):
                        raise ValueError("Unknown repetition mode '%s': it must be either an integer, \
                            the symbol '+' or '*', or an int variable already defined in class." % mode)
                self._lines.append(FormatLine( fields, self ))

    def name(self):
        return self._field.name

    def typeName(self):
        return self._field.typeName

    def parent(self):
        """ The parent of this object """
        return self._parent

    def lines(self):
        """ Return a list of FormatLine objects, each representing a line in this field.
        Empty line denotes a line without any field. """
        return self._lines

    def instanceRepetitionModeString(self):
        mode = self._field.instanceRepetitionModeString
        try:
            return int(mode)
        except ValueError as e:
            return mode

    def shouldSeparateInstancesByAdditionalNewline(self):
        return self._field.shouldSeparateInstancesByAdditionalNewline

    def isPrimitive(self):
        return isPrimitive(self._field.typeName)

    def isInteger(self):
        return isInteger(self._field.typeName)

    def isFloat(self):
        return isFloat(self._field.typeName)

    def isString(self):
        return isString(self._field.typeName)

    def isBool(self):
        return isBool(self._field.typeName)

    def isList(self):
        return isList(self._field.typeName)

    def listType(self):
        if self.isList():
            return listType(self._field.typeName)
        else:
            return None

    def __str__(self):
        s = ""
        if self.isPrimitive():
            s += "%s:%s" % ( self.name(), self.typeName() )
            if self.instanceRepetitionModeString():
                s += ":%s" % self.instanceRepetitionModeString()
                if self.shouldSeparateInstancesByAdditionalNewline():
                    s += "!"
        else:
            for index, line in enumerate(self.lines()):
                s += str(line)
                if index < len(self.lines()) - 1:
                    s += "\n"
        return s

class FormatLine:
    """ Representing a line in a class declaration or body of the format file.
    May contains zero or more fields. """
    def __init__( self, fields, container ):
        self._fields = fields
        # container is the FormatField object representing the class field that contains this line
        self._container = container
        self._currentIndex = 0
        # Repetition string only makes sense when a line has exactly one field
        self._repetitionString = fields[0].instanceRepetitionModeString() if len(fields) == 1 else ""
        self._isSplitByNewline = fields[0].shouldSeparateInstancesByAdditionalNewline() if \
            len(fields) == 1 else "" if len(fields) == 1 else ""

    def container(self):
        return self._container

    def isEmpty(self):
        return len(self._fields) == 0

    def repetitionString(self):
        return self._repetitionString

    def isZeroOrMoreRepetition(self):
        return self._repetitionString == StringConstants.LINE_ZERO_OR_MORE

    def isONEOrMoreRepetition(self):
        return self._repetitionString == StringConstants.LINE_ONE_OR_MORE

    def isIntegerRepetition(self):
        try:
            int(self._repetitionString)
            return True
        except ValueError as e:
            # Failed to cast to int, it's not int
            return False

    def isVariableRepetition(self):
        return ( not self.isZeroOrMoreRepetition() and
            not self.isONEOrMoreRepetition() and
            not self.isIntegerRepetition() )

    def isSplitByNewline(self):
        return self._isSplitByNewline

    def __iter__(self):
        return self

    def next(self):
        if self._currentIndex < len(self._fields):
            self._currentIndex += 1
            return self._fields[self._currentIndex - 1]
        else:
            # Reset the counter so we can use this in more than one for loop
            self._currentIndex = 0
            raise StopIteration

    def __str__(self):
        s = ""
        for f in self:
            s += str(f) + " "
        return s

def getFormat(fileName="examples/graph_example"):
    from parser import HeimerFormatFileParser
    p = HeimerFormatFileParser(fileName)
    return HeimerFormat(p.objectModel)
