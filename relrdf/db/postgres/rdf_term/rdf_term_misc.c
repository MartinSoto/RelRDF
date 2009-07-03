
#include "rdf_term.h"

#include "access/hash.h"

inline uint32_t arith_result_type(uint32_t type_id1, uint32_t type_id2);

/* Arithmetic operators */

inline uint32_t
arith_result_type(uint32_t type_id1, uint32_t type_id2)
{

	/* Must be compatible */
	if(!types_compatible(type_id1, type_id2))
		return 0;
	
	/* Most both be numeric types */
	if(!is_num_type(type_id1) || !is_num_type(type_id2))
		return 0;	

	/* Very rough approximation of type promotion: assume
	   lower number means higher priority */
	if(type_id1 < type_id2)
		return type_id1;
	else
		return type_id2;
}

PG_FUNCTION_INFO_V1(rdf_term_mul);
Datum
rdf_term_mul(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	uint32_t type_id = arith_result_type(term1->type_id, term2->type_id);
	if(!type_id)
		PG_RETURN_NULL();
		
	PG_RETURN_RDF_TERM(create_term_from_num(type_id, term1->num * term2->num));
}

PG_FUNCTION_INFO_V1(rdf_term_div);
Datum
rdf_term_div(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	uint32_t type_id = arith_result_type(term1->type_id, term2->type_id);
	if(!type_id)
		PG_RETURN_NULL();
	
	/* TODO: Per SPARQL standard we should make an exception here for the case
	         where both operands are of type xsd:integer... */
	
	PG_RETURN_RDF_TERM(create_term_from_num(type_id, term1->num / term2->num));
}

PG_FUNCTION_INFO_V1(rdf_term_add);
Datum
rdf_term_add(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	uint32_t type_id = arith_result_type(term1->type_id, term2->type_id);
	if(!type_id)
		PG_RETURN_NULL();
		
	PG_RETURN_RDF_TERM(create_term_from_num(type_id, term1->num + term2->num));
}

PG_FUNCTION_INFO_V1(rdf_term_sub);
Datum
rdf_term_sub(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	uint32_t type_id = arith_result_type(term1->type_id, term2->type_id);
	if(!type_id)
		PG_RETURN_NULL();
		
	PG_RETURN_RDF_TERM(create_term_from_num(type_id, term1->num - term2->num));
}

PG_FUNCTION_INFO_V1(rdf_term_unary_plus);
Datum
rdf_term_unary_plus(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);

	if(!is_num_type(term->type_id))		
		PG_RETURN_NULL();
		
	PG_RETURN_RDF_TERM(term);
}

PG_FUNCTION_INFO_V1(rdf_term_unary_minus);
Datum
rdf_term_unary_minus(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);

	if(!is_num_type(term->type_id))		
		PG_RETURN_NULL();
		
	PG_RETURN_RDF_TERM(create_term_from_num(term->type_id, -term->num));
}

/* Misc */

PG_FUNCTION_INFO_V1(rdf_term_lang_matches);
Datum
rdf_term_lang_matches(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);
	bool result;
	
	// Must both be simple literals
	if(term1->type_id != 1 || term2->type_id != 1)
		PG_RETURN_NULL();
	  
	// '*' matches everything that's non-empty
	if(!strcmp(term2->text, "*"))
	{
		result = *term1->text;
	}
	else
	{
		// Prefix test
		result = !strncasecmp(term1->text, term2->text, get_text_len(term2));
	}
	
	PG_RETURN_RDF_TERM(create_term_bool(result));
}

PG_FUNCTION_INFO_V1(rdf_term_hash);
Datum
rdf_term_hash(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);	
	uint32_t type_id = term->type_id;
	
	/* Values of compatible types must have the same hash value */
	Datum hash = hash_uint32(type_id & TYPE_COMPATIBLE_MASK);
	
	/* Hash the rest using hash_any
	
	   Note that we might hash a double value here, which might
	   be dangerous because that's not a canoncial representation
	   of a given number (consider +0 / -0, for example) */
	if(is_text_type(type_id))
		hash |= hash_any(
			(unsigned char *) term + RDF_TERM_HEADER_SIZE,
			VARSIZE(term) - RDF_TERM_HEADER_SIZE);
	else
		hash |= hash_any(
			(unsigned char *) &term->num,
			sizeof(term->num));
	
	return hash;
}
