
#include "rdf_term.h"

#include <math.h>

/* == Compare == */

inline int
compare_terms(RdfTerm *term1, RdfTerm *term2)
{

	/* Types compatible? Use (somewhat arbitrary) type order otherwise. */
	if(!types_compatible(term1->type_id, term2->type_id))
		return (term1->type_id < term2->type_id ? -1 : 1);
	
	/* Numerical type? */
	if(is_num_type(term1->type_id))
	{
		if(term1->num < term2->num)
			return -1;
		else if(term1->num == term2->num)
			return 0;
		else
			return 1;
	}
		
	/* Date/Time type? */
	if(is_date_time_type(term1->type_id))
	{
		if(term1->time < term2->time)
			return -1;
		else if(term1->time == term2->time)
			if(term1->time_have_tz < term2->time_have_tz)
				return -1;
			else if(term1->time_have_tz == term2->time_have_tz)
				return 0;
			else
				return 1;
		else
			return 1;
	}
	
	/* Internal type? All these are compatible, but unequal,
	  /except/ for xsd:string and simple literals */
	if(term1->type_id < term2->type_id)
	{
		if(term1->type_id != TYPE_ID_SIMPLE_LIT || term2->type_id != TYPE_ID_STRING)
			return -1;
	}
	else if(term1->type_id > term2->type_id)
	{
		if(term1->type_id != TYPE_ID_STRING || term2->type_id != TYPE_ID_SIMPLE_LIT)
			return 1;
	}
  
	/* Compare textual */
	return strcoll(term1->text, term2->text);
}

/* == Boolean operations == */

inline bool
to_bool(RdfTerm *term)
{
	if(is_num_type(term->type_id))
	{
		return isnan(term->num) || term->num != 0.0f;
	}
	else if(term->type_id == TYPE_ID_BOOL)
	{
		return strcoll(term->text, "true") == 0;
	}
	else
	{
		return get_text_len(term) > 0; 
	}
}

inline RdfTerm *
create_term_bool(bool flag)
{
	if(flag)
		return create_term_text(TYPE_ID_BOOL, "true", 4);
	else
		return create_term_text(TYPE_ID_BOOL, "false", 5);
}

/* Comparison operators */

PG_FUNCTION_INFO_V1(rdf_term_types_check_compatible);
Datum
rdf_term_types_check_compatible(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	if(!types_compatible(term1->type_id, term2->type_id))
	  PG_RETURN_NULL();
	/* It's a type error to compare values of unknown
	   type that are not equal */
  if(term1->type_id >= STORAGE_TYPE_UNKNOWN)
    if(compare_terms(term1, term2) != 0)
      PG_RETURN_NULL();
	    
	PG_RETURN_BOOL(true);
}

PG_FUNCTION_INFO_V1(rdf_term_types_check_incompatible);
Datum
rdf_term_types_check_incompatible(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	if(!types_compatible(term1->type_id, term2->type_id))
	  PG_RETURN_NULL();	  
  if(term1->type_id >= STORAGE_TYPE_UNKNOWN)
    if(compare_terms(term1, term2) != 0)
      PG_RETURN_NULL();
	    
	PG_RETURN_BOOL(false);
}

PG_FUNCTION_INFO_V1(rdf_term_compare);
Datum
rdf_term_compare(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_INT32(compare_terms(term1, term2));	
}

PG_FUNCTION_INFO_V1(rdf_term_less);
Datum
rdf_term_less(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) < 0);	
}

PG_FUNCTION_INFO_V1(rdf_term_less_equal);
Datum
rdf_term_less_equal(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) <= 0);	
}

PG_FUNCTION_INFO_V1(rdf_term_equal);
Datum
rdf_term_equal(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) == 0);	
}

PG_FUNCTION_INFO_V1(rdf_term_different);
Datum
rdf_term_different(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) != 0);	
}

PG_FUNCTION_INFO_V1(rdf_term_greater_equal);
Datum
rdf_term_greater_equal(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) >= 0);	
}

PG_FUNCTION_INFO_V1(rdf_term_greater);
Datum
rdf_term_greater(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	
	PG_RETURN_BOOL(compare_terms(term1, term2) > 0);	
}

/* Boolean operators and predicates */

PG_FUNCTION_INFO_V1(rdf_term_to_bool);
Datum
rdf_term_to_bool(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = to_bool(term);

	PG_RETURN_BOOL(result);
}

PG_FUNCTION_INFO_V1(rdf_term_not_raw);
Datum
rdf_term_not_raw(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = !to_bool(term);

	PG_RETURN_BOOL(result);
}

PG_FUNCTION_INFO_V1(rdf_term_not);
Datum
rdf_term_not(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = !to_bool(term);

	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_and);
Datum
rdf_term_and(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	bool result = to_bool(term1) && to_bool(term2);

	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_or);
Datum
rdf_term_or(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	bool result = to_bool(term1) || to_bool(term2);

	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_bound);
Datum
rdf_term_bound(PG_FUNCTION_ARGS)
{
	PG_RETURN_RDF_TERM(create_term_bool(!PG_ARGISNULL(0)));
}

PG_FUNCTION_INFO_V1(rdf_term_is_uri);
Datum
rdf_term_is_uri(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = is_resource(term, true, false);
	
	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_is_bnode);
Datum
rdf_term_is_bnode(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = is_resource(term, false, true);
	
	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_is_literal);
Datum
rdf_term_is_literal(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	bool result = !is_resource(term, true, true);
	
	PG_RETURN_RDF_TERM(create_term_bool(result));
}

