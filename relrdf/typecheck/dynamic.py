
from relrdf import commonns
from relrdf.expression import nodes, rewrite

from typeexpr import commonType, LiteralType, genericLiteralType, \
     BlankNodeType, blankNodeType, ResourceType, resourceType, RdfNodeType

class DynTypeTransl(rewrite.ExpressionTransformer):
    """An expression translator that replaces DynType node
    with known type information where possible"""

    __slots__ = ()

    def __init__(self):
        super(DynTypeTransl, self).__init__(prePrefix='pre')

    def preDynType(self, expr):
        return (self._dynTypeExpr(expr[0].copy()),)

    def DynType(self, expr, subexpr):
        return subexpr

    def _dynTypeExpr(self, expr):
        typeExpr = expr.staticType        
        if isinstance(typeExpr, LiteralType):
            # FIXME:Search for the actual type id.
            result = nodes.Type(genericLiteralType)
        elif isinstance(typeExpr, BlankNodeType):
            result = nodes.Type(blankNodeType)
        elif isinstance(typeExpr, ResourceType):
            result = nodes.Type(resourceType)
        else:
            # This expression has a generic type whose dynamic form
            # must be resolved later by the mapper.
            #
            # FIXME: Consider using another node type here instead of
            # DynType (MapperDynType?)
            result = nodes.DynType(expr)
        result.staticType = resourceType
        return result

class TypeCheckCollector(rewrite.ExpressionProcessor):
    """An expression processor that collects needed type compatibility checks
    for an expression."""

    __slots__ = ('typechecks', )

    def __init__(self):
        self.typechecks = []
        
        super(TypeCheckCollector, self).__init__(prePrefix='pre')
    
    def _addTypecheck(self, expr, *transfSubexprs):
        
        # Dynamically check wether the two values are type-compatible
        # (provided both actually are some sort of RDF node)
        common = commonType(*expr)
        if isinstance(common, RdfNodeType):
            subexprCopies = [e.copy() for e in expr];
            self.typechecks.append(nodes.TypeCompatible(*subexprCopies))

    # TODO: Only checking comparisons. Should be expanded in future.
    Equal = _addTypecheck
    LessThan = _addTypecheck
    LessThanOrEqual = _addTypecheck
    GreaterThan = _addTypecheck
    GreaterThanOrEqual = _addTypecheck
    Different = _addTypecheck
    
    def Default(self, expr, *sexpr):
        pass
    
class SelectTypeCheckTransformer(rewrite.ExpressionTransformer):
    """An expression transformer that adds dynamic type checks to
    all select predicates."""

    def __init__(self):
        super(SelectTypeCheckTransformer, self).__init__(prePrefix='pre')
    
    def Select(self, expr, rel, pred):
        
        # Collect type checks
        collector = TypeCheckCollector();
        collector.process(pred)
        
        # Add dynamic type checks
        if collector.typechecks != []:
            pred = nodes.And(pred, *collector.typechecks)
        
        return nodes.Select(rel, pred)
        
    
def dynTypeCheckTranslate(expr):

    # Replace DynType nodes where possible
    dynTypeTrans = DynTypeTransl()
    expr = dynTypeTrans.process(expr)
    
    # Insert type checks into predicates
    typeCheckTrans = SelectTypeCheckTransformer()
    expr = typeCheckTrans.process(expr)

    return expr
