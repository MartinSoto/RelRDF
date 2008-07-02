
#include "postgres.h"
#include "fmgr.h"
#include "libpq/pqformat.h"
#include "access/hash.h"

#include <stdint.h>
#include <assert.h>

#ifdef PG_MODULE_MAGIC
PG_MODULE_MAGIC;
#endif

/* RDF term structure */
typedef struct {

  /* Needed by PostgreSQL */
	char vl_len_[4];
	
	/* Type IDs, see below */
	uint32_t type_id;
	
	/* Language ID (future) */
	/* uint32_t lang_id; */
	
	/* Actual value */
	union {
		double num;
		char text[1];
	};
	
} RdfTerm;

#define RDF_TERM_NUM_SIZE 		sizeof( ((RdfTerm *)0)->num )
#define RDF_TERM_HEADER_SIZE	(sizeof(RdfTerm) - RDF_TERM_NUM_SIZE)

/*
	== Type classification ==
	
	Types whose IDs only differ in the least-
	significant byte are considered to be	comparable.

	Types with an ID lower than 0x0001000 are numeric
	types.
*/

#define TYPE_COMPATIBLE_MASK ((uint32_t) 0xFFFFFF00)

#define STORAGE_TYPE_MASK    ((uint32_t) 0xFFFFF000)
#define STORAGE_TYPE_IRI     ((uint32_t) 0x00000000)
#define STORAGE_TYPE_NUM     ((uint32_t) 0x00001000)

inline bool
is_num_type(uint32_t type_id)
{
	return (type_id & STORAGE_TYPE_MASK) == STORAGE_TYPE_NUM;
}

inline bool
is_text_type(uint32_t type_id)
{
	/* IRIs are stored as text, too */
	return !is_num_type(type_id);
}

inline bool
types_compatible(uint32_t type_id1, uint32_t type_id2)
{
	return (type_id1 & TYPE_COMPATIBLE_MASK) ==
	       (type_id2 & TYPE_COMPATIBLE_MASK);
}

/* == Acessors == */

/* Returns the string length of the value */
inline int32_t
get_text_len(RdfTerm *term)
{
	return VARSIZE(term) - RDF_TERM_HEADER_SIZE - sizeof(char);
}

/* == Constructors == */

RdfTerm *
create_term_num(uint32_t type_id, double num)
{
	/* Allocate */
	uint32_t size = RDF_TERM_HEADER_SIZE + RDF_TERM_NUM_SIZE;
	RdfTerm *term = (RdfTerm *) palloc(size);
	
	/* Initialize */
	SET_VARSIZE(term, size);
	term->type_id = type_id;
	term->num = num;
	
	return term;
}

RdfTerm *
create_term_text(uint32_t type_id, char *text, size_t len)
{
	/* Allocate */
	uint32_t size = RDF_TERM_HEADER_SIZE + len + sizeof(char);
	RdfTerm *term = (RdfTerm *) palloc(size);
	
	/* Initialize */
	SET_VARSIZE(term, size);
	term->type_id = type_id;
	memcpy((void *) term->text,
	       (void *) text,
	       len);
	       
	/* 
		Null-terminate the string, so we can use strcoll later on.
		
		This is a hack, but I think it's better than allocating a new
		copy of the string for each comparison. That's what the PostgreSQL
		seems to do internally.
	*/
	term->text[len] = '\0';
	
	return term;
}

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
		
	/* Otherwise: textual type */
	return strcoll(term1->text, term2->text);	
}

/* == PostgreSQL interface == */

/* TODO: Maybe optimize this to use PG_GETARG_VARLENA_PP */
#define PG_GETARG_RDF_TERM(x) ((RdfTerm *) PG_GETARG_VARLENA_P(x))
#define PG_RETURN_RDF_TERM(x) PG_RETURN_POINTER(x)

/* Datatype representation */

PG_FUNCTION_INFO_V1(rdf_term_in);
Datum
rdf_term_in(PG_FUNCTION_ARGS)
{
	char *str = PG_GETARG_CSTRING(0);
	char *pos = str;
	char *start;
	
	double num;
	
	uint32_t type_id, len;
	
	RdfTerm *term;
	
	/* Go over whitespace */
	while(isblank(*pos))
		pos += 1;

	/* Text type? */
	if(*pos == '\'')
	{
		/* Search for end */
		start = pos = pos + 1;
		while(*pos && *pos != '\'')
			pos += 1;
		
		/* Invalid? */
		if(!*pos)
			PG_RETURN_NULL();
		
		/* Scan type ID */
		len = pos-start; pos += 1;
		if(1 != sscanf(pos, "^^%x", &type_id))
			PG_RETURN_NULL();
		if(is_num_type(type_id))
			PG_RETURN_NULL();
			
		/* Create term (TODO: escaping)*/
		term = create_term_text(type_id, start, len);
	}

	/* Number type? */
	else if(sscanf(pos, "%lg%n", &num, &len) > 0)
	{
		/* Advance pointer */
		pos += len;
		
		/* Scan type ID */
		if(1 != sscanf(pos, "^^%x", &type_id))
			PG_RETURN_NULL();
		if(is_text_type(type_id))
			PG_RETURN_NULL();
			
		/* Create term */
		term = create_term_num(type_id, num);
	}
	
	/* Invalid input */
	else
		PG_RETURN_NULL();
	
	PG_RETURN_RDF_TERM(term);
}

PG_FUNCTION_INFO_V1(rdf_term_out);
Datum
rdf_term_out(PG_FUNCTION_ARGS)
{
	RdfTerm *term = (RdfTerm *) PG_GETARG_RDF_TERM(0);
	size_t len;
	char *result, *pos;
	
	/* Text type? */
	if(is_text_type(term->type_id))
	{

		/* Allocate a buffer large enough */
		len = get_text_len(term);
		result = (char *) palloc(1 + len + 1 + 2 + 10 + 1);
		
		/* Construct string (TODO: escaping) */
		pos = result;	
		
		*pos = '\''; pos += 1;
		memcpy((void *) pos,
		       (void *) term->text,
		       len);
		pos += len;		
		*pos = '\''; pos += 1;
		
		snprintf(pos, 2 + 10 + 1, "^^%x", term->type_id);
		
	}
	else
	{
	
		/* Allocate a buffer large enough */
		len = 100 + 2 + 10 + 1;
		result = (char *) palloc(len);
	
		/* Construct string */
		snprintf(result, len, "%lg^^%x", term->num, term->type_id);
		
	}
	
	PG_RETURN_CSTRING(result);	
}

PG_FUNCTION_INFO_V1(rdf_term_recv);
Datum
rdf_term_recv(PG_FUNCTION_ARGS)
{
	StringInfo buf = (StringInfo) PG_GETARG_POINTER(0);
	
	uint32_t type_id;
	double num; char *text;	int len;
	RdfTerm *term;
	
	/* Read type ID */
	type_id = (uint32_t) pq_getmsgint(buf, 4);
	
	/* Text type? */
	if(is_text_type(type_id))
	{
			
		/* Read length */
		len = (uint32_t) pq_getmsgint(buf, 4);

		/* Read text and actual length after decoding */
		text = pq_getmsgtext(buf, len, &len);
		
		/* Allocate term */
		term = create_term_text(type_id, text, len);
		
		/* Free text */
		pfree(text);
		
	}
	else
	{

		/* Read num */
		num = pq_getmsgfloat8(buf);
		
		/* Allocate term */
		term = create_term_num(type_id, num);
		
	}
	
	/* Done */
	pq_getmsgend(buf);
	PG_RETURN_RDF_TERM(term);
}

PG_FUNCTION_INFO_V1(rdf_term_send);
Datum
rdf_term_send(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	
	uint32_t len;
	StringInfoData buf;
	
	/* Send type ID first */
	pq_begintypsend(&buf);
	pq_sendint(&buf, term->type_id, 4);
	
	/* Text type? */
	if(is_text_type(term->type_id))
	{
	
		/* Write length and text*/
		len = get_text_len(term);
		pq_sendint(&buf, len, 4);
		pq_sendtext(&buf, term->text, len);
		
	}
	else
	{
	
		/* Just write numerical value */
		pq_sendfloat8(&buf, term->num);
	
	}
	
	/* Done */
	PG_RETURN_BYTEA_P(pq_endtypsend(&buf));
}

/* Constructors */

PG_FUNCTION_INFO_V1(rdf_term_double);
Datum
rdf_term_double(PG_FUNCTION_ARGS)
{
	int32 type_id = PG_GETARG_INT32(0);
	float8 num = PG_GETARG_FLOAT8(1);
	RdfTerm *term;
	
	/* Make sure the type ID is valid */
	if(!is_num_type(type_id))
		PG_RETURN_NULL();

	/* Create the appropriate term */
	term = create_term_num(type_id, (double) num);		
	PG_RETURN_RDF_TERM(term);
}

PG_FUNCTION_INFO_V1(rdf_term_text);
Datum
rdf_term_text(PG_FUNCTION_ARGS)
{
	int32 type_id = PG_GETARG_INT32(0);
	text *txt = PG_GETARG_TEXT_PP(1);
	RdfTerm *term;

	/* Make sure the type ID is valid */
	if(!is_text_type(type_id))
		PG_RETURN_NULL();

	/* Create the appropriate term */
	term = create_term_text(type_id,
		VARDATA_ANY(txt),
		VARSIZE_ANY_EXHDR(txt));		
	PG_RETURN_RDF_TERM(term);
}

/* Accessors */

PG_FUNCTION_INFO_V1(rdf_term_get_type_id);
Datum
rdf_term_get_type_id(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);

	PG_RETURN_UINT32(term->type_id);
}

PG_FUNCTION_INFO_V1(rdf_term_is_num_type_t);
Datum
rdf_term_is_num_type_t(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);

	PG_RETURN_BOOL(is_num_type(term->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_is_num_type_i);
Datum
rdf_term_is_num_type_i(PG_FUNCTION_ARGS)
{
	uint32_t type_id = PG_GETARG_UINT32(0);

	PG_RETURN_BOOL(is_num_type(type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_is_text_type_t);
Datum
rdf_term_is_text_type_t(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);

	PG_RETURN_BOOL(is_text_type(term->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_is_text_type_i);
Datum
rdf_term_is_text_type_i(PG_FUNCTION_ARGS)
{
	uint32_t type_id = PG_GETARG_UINT32(0);

	PG_RETURN_BOOL(is_text_type(type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_to_string);
Datum
rdf_term_to_string(PG_FUNCTION_ARGS)
{
	/* Return data formatted as string - similar to rdf_term_out, but
	   without type indentifier */

	RdfTerm *term = (RdfTerm *) PG_GETARG_RDF_TERM(0);
	size_t len;
	char *result;
	
	/* Text type? */
	if(is_text_type(term->type_id))
	{
	
		/* Copy text */
		len = get_text_len(term);
		result = (char *) palloc(len + 1);
		
		memcpy((void *) result, (void *) term->text, len);
		result[len] = '\0';
		
	}
	else
	{
	
		/* Print into buffer */
		len = 100 + 1;
		result = (char *) palloc(len);
	
		snprintf(result, len, "%lg", term->num);
	
	}
	
	PG_RETURN_CSTRING(result);	
}

/* Operators */

PG_FUNCTION_INFO_V1(rdf_term_types_compatible_tt);
Datum
rdf_term_types_compatible_tt(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	PG_RETURN_BOOL(types_compatible(term1->type_id, term2->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_types_incompatible_tt);
Datum
rdf_term_types_incompatible_tt(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	PG_RETURN_BOOL(!types_compatible(term1->type_id, term2->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_types_compatible_it);
Datum
rdf_term_types_compatible_it(PG_FUNCTION_ARGS)
{
	uint32_t type_id1 = PG_GETARG_UINT32(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	PG_RETURN_BOOL(types_compatible(type_id1, term2->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_types_incompatible_it);
Datum
rdf_term_types_incompatible_it(PG_FUNCTION_ARGS)
{
	uint32_t type_id1 = PG_GETARG_UINT32(0);
	RdfTerm *term2 = PG_GETARG_RDF_TERM(1);

	PG_RETURN_BOOL(!types_compatible(type_id1, term2->type_id));
}

PG_FUNCTION_INFO_V1(rdf_term_types_compatible_ti);
Datum
rdf_term_types_compatible_ti(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	uint32_t type_id2 = PG_GETARG_UINT32(1);

	PG_RETURN_BOOL(types_compatible(term1->type_id, type_id2));
}

PG_FUNCTION_INFO_V1(rdf_term_types_incompatible_ti);
Datum
rdf_term_types_incompatible_ti(PG_FUNCTION_ARGS)
{
	RdfTerm *term1 = PG_GETARG_RDF_TERM(0);
	uint32_t type_id2 = PG_GETARG_UINT32(1);

	PG_RETURN_BOOL(!types_compatible(term1->type_id, type_id2));
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

/* Hash function */

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
	hash |= hash_any(
		(unsigned char *) term + RDF_TERM_HEADER_SIZE,
		VARSIZE(term) - RDF_TERM_HEADER_SIZE);
	
	return hash;
}



