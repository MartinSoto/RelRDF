
#ifndef __RDF_TERM_H__
#define __RDF_TERM_H__

#include "postgres.h"
#include "fmgr.h"

#include <time.h>
#include <stdint.h>

/*
	== Type classification ==
	
	There's a lot of information and "magic" in type IDs. The
	following must be understood before assigning type IDs:
	* The type ID must differentiate the following literal types:
	  -> resources (here: IRIs and blank nodes)
	  -> simple literals
	  -> plain literals (by language tag)
	  -> generic literals (by data type URI)
	* It must be clear which type IDs are compatible
	  (comparison is not a type error)
	* There needs to be a defined order in which the types should
	  appear when an ORDER BY clause is used (see section 9.1 of
	  the SPARQL standard).

	This leads to the following partition of the type ID space:
	* 0x0000        -> resources (IRI + blank nodes)
	* 0x0001        -> simple literals
	* 0x0002        -> literals of type xsd:string
	* 0x0003-0x0fff -> plain literals
	* 0x1000-0x1fff -> numeric types
	* 0x2000        -> boolean type
	* 0x3000-0x3fff -> date/time types
	* >= 0x4000     -> unsupported types
	
	Note that all type IDs greater or equal to 0x1000 can be considered
	comparable iff everything but the last 12 bits is equal (so there can
	be a maximum of 4096 comparable types in this system).

	Also note that all type IDs greater or equal to 0x1000 must have an
	associated type URI, while all type IDs from 0x0002 to 0x0fff must
	have a language tag. This mapping isn't done here, though.
*/

#define TYPE_ID_IRI          ((uint32_t) 0x00000000)
#define TYPE_ID_SIMPLE_LIT   ((uint32_t) 0x00000001)
#define TYPE_ID_STRING       ((uint32_t) 0x00000002)

#define TYPE_ID_BOOL         ((uint32_t) 0x00002000)

#define TYPE_ID_DATETIME     ((uint32_t) 0x00003000)
#define TYPE_ID_DATE         ((uint32_t) 0x00003100)
#define TYPE_ID_TIME         ((uint32_t) 0x00003200)

#define TYPE_COMPATIBLE_MASK ((uint32_t) 0xFFFFFF00)

#define STORAGE_TYPE_MASK    ((uint32_t) 0xFFFFF000)
#define STORAGE_TYPE_INTERNAL ((uint32_t) 0x00000000)
#define STORAGE_TYPE_NUM     ((uint32_t) 0x00001000)
#define STORAGE_TYPE_DT      ((uint32_t) 0x00003000)
#define STORAGE_TYPE_UNKNOWN ((uint32_t) 0x00004000)

/* Prefix used for blank node resources */
#define BLANK_NODE_PREFIX    "bnode:"

/* RDF term structure */
typedef struct {

  /* Needed by PostgreSQL */
	char vl_len_[4];
	
	/* Type IDs, see below */
	uint32_t type_id;
	
	/* Value representation */
	union {		
		double num;
		time_t time;
	};
	bool time_have_tz;
	
	/* Original */
	char text[1];
	
} RdfTerm;

/* == Declarations == */

static inline bool is_num_type(uint32_t type_id);
static inline bool is_date_time_type(uint32_t type_id);
static inline bool is_text_type(uint32_t type_id);
static inline bool types_compatible(uint32_t type_id1, uint32_t type_id2);
static inline int32_t get_text_len(RdfTerm *term);
static inline bool is_resource(RdfTerm *term, bool uri, bool bnode);

RdfTerm *create_term(uint32_t type_id, char *text, size_t len);
RdfTerm *create_term_text(uint32_t type_id, char *text, size_t len);
RdfTerm *create_term_num(uint32_t type_id, char *text, size_t len);
RdfTerm *create_term_date_time(uint32_t type_id, char *text, size_t len);
RdfTerm *create_term_by_id(uint32_t type_id, char *text, size_t len);
RdfTerm *create_term_from_num(uint32_t type_id, double num);

Datum rdf_term_in(PG_FUNCTION_ARGS);
Datum rdf_term_out(PG_FUNCTION_ARGS);
Datum rdf_term_recv(PG_FUNCTION_ARGS);
Datum rdf_term_send(PG_FUNCTION_ARGS);
Datum rdf_term_create(PG_FUNCTION_ARGS);
Datum rdf_term_cast(PG_FUNCTION_ARGS);
Datum rdf_term_get_type_id(PG_FUNCTION_ARGS);
Datum rdf_term_get_data_type_id(PG_FUNCTION_ARGS);
Datum rdf_term_get_language_id(PG_FUNCTION_ARGS);
Datum rdf_term_to_string(PG_FUNCTION_ARGS);

int compare_terms(RdfTerm *term1, RdfTerm *term2);
bool to_bool(RdfTerm *term);
RdfTerm *create_term_bool(bool flag);

Datum rdf_term_types_check_compatible(PG_FUNCTION_ARGS);
Datum rdf_term_types_check_incompatible(PG_FUNCTION_ARGS);
Datum rdf_term_compare(PG_FUNCTION_ARGS);
Datum rdf_term_less(PG_FUNCTION_ARGS);
Datum rdf_term_less_equal(PG_FUNCTION_ARGS);
Datum rdf_term_equal(PG_FUNCTION_ARGS);
Datum rdf_term_different(PG_FUNCTION_ARGS);
Datum rdf_term_greater_equal(PG_FUNCTION_ARGS);
Datum rdf_term_greater(PG_FUNCTION_ARGS);
Datum rdf_term_to_bool(PG_FUNCTION_ARGS);
Datum rdf_term_not_raw(PG_FUNCTION_ARGS);
Datum rdf_term_not(PG_FUNCTION_ARGS);
Datum rdf_term_and(PG_FUNCTION_ARGS);
Datum rdf_term_or(PG_FUNCTION_ARGS);
Datum rdf_term_bound(PG_FUNCTION_ARGS);
Datum rdf_term_is_uri(PG_FUNCTION_ARGS);
Datum rdf_term_is_bnode(PG_FUNCTION_ARGS);
Datum rdf_term_is_literal(PG_FUNCTION_ARGS);

Datum rdf_term_mul(PG_FUNCTION_ARGS);
Datum rdf_term_div(PG_FUNCTION_ARGS);
Datum rdf_term_add(PG_FUNCTION_ARGS);
Datum rdf_term_sub(PG_FUNCTION_ARGS);
Datum rdf_term_unary_plus(PG_FUNCTION_ARGS);
Datum rdf_term_unary_minus(PG_FUNCTION_ARGS);
Datum rdf_term_lang_matches(PG_FUNCTION_ARGS);
Datum rdf_term_hash(PG_FUNCTION_ARGS);

/* == PostgreSQL interface == */

/* TODO: Maybe optimize this to use PG_GETARG_VARLENA_PP */
#define PG_GETARG_RDF_TERM(x) ((RdfTerm *) PG_GETARG_VARLENA_P(x))
#define PG_RETURN_RDF_TERM(x) PG_RETURN_POINTER(x)

/* == Definitions == */

#define RDF_TERM_HEADER_SIZE	(sizeof(RdfTerm) - sizeof(char))

static inline bool
is_num_type(uint32_t type_id)
{
	return (type_id & STORAGE_TYPE_MASK) == STORAGE_TYPE_NUM;
}

static inline bool
is_date_time_type(uint32_t type_id)
{
	return (type_id & STORAGE_TYPE_MASK) == STORAGE_TYPE_DT;
}

static inline bool
is_text_type(uint32_t type_id)
{
	/* IRIs are stored as text, too */
	return !is_num_type(type_id) && !is_date_time_type(type_id);
}

static inline bool
types_compatible(uint32_t type_id1, uint32_t type_id2)
{
	return (type_id1 & TYPE_COMPATIBLE_MASK) ==
	       (type_id2 & TYPE_COMPATIBLE_MASK);
}

/* == Acessors == */

/* Returns the string length of the value */
static inline int32_t
get_text_len(RdfTerm *term)
{
	return VARSIZE(term) - RDF_TERM_HEADER_SIZE - sizeof(char);
}

/* Tests wether a node is some type of resource */
static inline bool
is_resource(RdfTerm *term, bool uri, bool bnode)
{
	int len = strlen(BLANK_NODE_PREFIX);	

	/* All resources have a type ID of 0 */
	if(term->type_id)
		return false;
	if(uri == bnode)
		return true;
    
	/* Compare prefix */
	if(get_text_len(term) >= len)
		if(strncmp(term->text, BLANK_NODE_PREFIX, len) == 0)
			return bnode;
  return uri;
}

#endif // __RDF_TERM_H__

