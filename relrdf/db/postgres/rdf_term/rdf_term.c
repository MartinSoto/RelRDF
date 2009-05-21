
#include "postgres.h"
#include "fmgr.h"
#include "libpq/pqformat.h"
#include "access/hash.h"

#include <stdint.h>
#include <assert.h>
#include <math.h>
#include <time.h>

#ifdef PG_MODULE_MAGIC
PG_MODULE_MAGIC;
#endif

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
	* There needs to be a difined order in which the types should
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

#define RDF_TERM_HEADER_SIZE	(sizeof(RdfTerm) - sizeof(char))

inline bool
is_num_type(uint32_t type_id)
{
	return (type_id & STORAGE_TYPE_MASK) == STORAGE_TYPE_NUM;
}

inline bool
is_date_time_type(uint32_t type_id)
{
	return (type_id & STORAGE_TYPE_MASK) == STORAGE_TYPE_DT;
}

inline bool
is_text_type(uint32_t type_id)
{
	/* IRIs are stored as text, too */
	return !is_num_type(type_id) && !is_date_time_type(type_id);
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

/* Tests wether a node is some type of resource */
inline bool
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

/* == Constructors == */

RdfTerm *
create_term(uint32_t type_id, char *text, size_t len)
{
	/* Allocate */
	uint32_t size = RDF_TERM_HEADER_SIZE + len + sizeof(char);
	RdfTerm *term = (RdfTerm *) palloc(size);
	memset(term, 0, size);
	
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

RdfTerm *
create_term_text(uint32_t type_id, char *text, size_t len)
{

	/* Additional check for boolean values */
	if(type_id == TYPE_ID_BOOL)
		if( (len != 4 || strncmp(text, "true", 4)) &&
		    (len != 5 || strncmp(text, "false", 5)) )
			return NULL;
		
	return create_term(type_id, text, len);
}

RdfTerm *
create_term_num(uint32_t type_id, char *text, size_t len)
{
	RdfTerm *term; size_t num_len;
	double num; char buf[12+1];

	/* Do not accept numbers that are too long */
	if(len > 12)
		return NULL;
	
	/* Parse the number */
	strncpy(buf, text, len); buf[len] = '\0';
	if(sscanf(buf, "%lg%n", &num, &num_len) < 1 || num_len != len)
		return NULL;
	
	/* Create the term */
	term = create_term(type_id, text, len);
	term->num = num;
	
	return term;
}


RdfTerm *
create_term_date_time(uint32_t type_id, char *text, size_t len)
{
	RdfTerm *term;
	int year=0, month=0, day=0,
	    hour=0, minute=0, second=0, fraction=0,
	    tz_hour=0, tz_minute=0;
	bool have_tz = false;
	struct tm tm; time_t t;
	int scan_len;
	char *pos;
	
	/* Copy data into buffer. Limit size of effencieny reasons. */
	char buf[40+1];	if(len > 30) len = 40;
	strncpy(buf, text, len); buf[len] = '\0';
	pos = buf;
	
	/* Scan date */
	if(type_id == TYPE_ID_DATETIME || type_id == TYPE_ID_DATE)
	{
		if(sscanf(pos, "%d-%d-%d%n", &year, &month, &day, &scan_len) < 3)
			return NULL;
		pos += scan_len;
	}
	
	/* Seperator */
	if(type_id == TYPE_ID_DATETIME)
	{
		if(*pos != 'T')
			return NULL;
		pos = pos + sizeof(char);
	}
	
	/* Scan time */
	if(type_id == TYPE_ID_DATETIME || type_id == TYPE_ID_TIME)
	{
		if(sscanf(pos, "%d:%d:%d%n", &hour, &minute, &second, &scan_len) < 3)
			return NULL;
		pos += scan_len;
		
		/* Fractions? */
		if(*pos == '.')
		{
			pos = pos + sizeof(char);
			if(sscanf(pos, "%d%n", &fraction, &scan_len) < 1)
				return NULL;
			pos += scan_len;
			
			/* Validate */
			if(fraction % 10 == 0)
				return NULL;
		}
	}
	
	/* Time zone (optional) */
	if(*pos == 'Z')
	{
		/* UTC time zone (standard) - so ignore it */
		pos = pos + sizeof(char);
		have_tz = true;
	}
	else if(*pos == '+' || *pos == '-')
	{
		
		/* Not allowed for time values */
		if(type_id == TYPE_ID_TIME)
			return NULL;
			
		/* Scan timezone data */
		if(sscanf(pos, "%d:%d%n", &tz_hour, &tz_minute, &scan_len) < 2)
			return NULL;
		pos = pos + scan_len;
		
		have_tz = true;
	}
	
	/* Must be at end */
	if(*pos)
		return NULL;
		
	/* 
	  Convert to seconds since the Epoch. This is obviously very rough:
	  * Fractions are stripped
	  * Might overflow and underflow (for year < 1900 for example)
	  * mktime() uses the local timezone, not the one given by tz_hour/tz_minute
	*/
	memset(&tm, 0, sizeof(tm));
	tm.tm_sec = second;
	tm.tm_min = minute;
	tm.tm_hour = hour;
	if(type_id != TYPE_ID_TIME)
	{
		tm.tm_mday = day;
		tm.tm_mon = month-1;
		tm.tm_year = year-1900;
	}
	else
	{
		tm.tm_mday = 1;
		tm.tm_year = 2; /* I have no idea why this is the lowest value that's accepted. */
	}
	t = mktime(&tm);
	
	if(t == (time_t) -1)
		return create_term_text(0, "mkt", 3);
		
	/* Create the term */
	term = create_term(type_id, text, len);
	term->time = t;
	term->time_have_tz = have_tz;
	
	return term;
}

RdfTerm *
create_term_by_id(uint32_t type_id, char *text, size_t len)
{
	if(is_num_type(type_id))
		return create_term_num(type_id, text, len);
	else if(is_date_time_type(type_id))
		return create_term_date_time(type_id, text, len);
	else
		return create_term_text(type_id, text, len);
}

RdfTerm *
create_term_from_num(uint32_t type_id, double num)
{
	RdfTerm *term;
	char text[12+1];

	/* Format number */
	size_t len = snprintf(text, 12, "%lg", num);
	if(len >= 12)
		return NULL;
	
	/* Create the term */
	term = create_term(type_id, text, len);
	term->num = num;
	
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
	
	uint32_t type_id, len;
	
	RdfTerm *term = NULL;
	
	/* Go over whitespace */
	while(isblank(*pos))
		pos += 1;

	/* Seperator? */
	if(*pos != '\'')
		PG_RETURN_NULL();
	
	
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
		
	/* Create term (TODO: escaping)*/
	term = create_term_by_id(type_id, start, len);
		
	/* Invalid input */
	if(!term)
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
	
	PG_RETURN_CSTRING(result);	
}

PG_FUNCTION_INFO_V1(rdf_term_recv);
Datum
rdf_term_recv(PG_FUNCTION_ARGS)
{
	StringInfo buf = (StringInfo) PG_GETARG_POINTER(0);
	
	uint32_t type_id;
	char *text;	int len;
	RdfTerm *term = NULL;
	
	/* Read type ID */
	type_id = (uint32_t) pq_getmsgint(buf, 4);
			
	/* Read length */
	len = (uint32_t) pq_getmsgint(buf, 4);

	/* Read text and actual length after decoding */
	text = pq_getmsgtext(buf, len, &len);
	
	/* Allocate term */
	term = create_term_by_id(type_id, text, len);
	
	/* Free text */
	pfree(text);
	
	/* Invalid input */
	if(!term)
		PG_RETURN_NULL();
		
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

PG_FUNCTION_INFO_V1(rdf_term_create);
Datum
rdf_term_create(PG_FUNCTION_ARGS)
{
	int32 type_id = PG_GETARG_INT32(0);
	text *data = PG_GETARG_TEXT_PP(1);
	char *text = VARDATA_ANY(data);
	size_t len = VARSIZE_ANY_EXHDR(data);
	RdfTerm *term = NULL;

	/* Create the appropriate term */
	term = create_term_by_id(type_id, text, len);
	
	/* Invalid? */
	if(!term)
	  PG_RETURN_NULL();
	
	PG_RETURN_RDF_TERM(term);
}

PG_FUNCTION_INFO_V1(rdf_term_cast);
Datum
rdf_term_cast(PG_FUNCTION_ARGS)
{
	int32 type_id = PG_GETARG_INT32(0);
	RdfTerm *old_term = PG_GETARG_RDF_TERM(1);
	RdfTerm *term = NULL;

	/* Create the appropriate term */
	term = create_term_by_id(type_id,
		old_term->text, get_text_len(old_term));
	
	/* Invalid? */
	if(!term)
	  PG_RETURN_NULL();
	
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

PG_FUNCTION_INFO_V1(rdf_term_get_data_type_id);
Datum
rdf_term_get_data_type_id(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	
	/* Only return type ID if it's a data type ID
	   (= should have an associated data type URI) */
	if(term->type_id <= ~STORAGE_TYPE_MASK)
		PG_RETURN_NULL();

	PG_RETURN_UINT32(term->type_id);
}


PG_FUNCTION_INFO_V1(rdf_term_get_language_id);
Datum
rdf_term_get_language_id(PG_FUNCTION_ARGS)
{
	RdfTerm *term = PG_GETARG_RDF_TERM(0);
	
	/* Only return type ID if it's a plain literal ID
	   (= should have an associated language tag) */
	if(term->type_id <= TYPE_ID_STRING || term->type_id > ~STORAGE_TYPE_MASK)
		PG_RETURN_NULL();

	PG_RETURN_UINT32(term->type_id);
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
	
	/* Copy text */
	len = get_text_len(term);
	result = (char *) palloc(len + 1);
	
	memcpy((void *) result, (void *) term->text, len);
	result[len] = '\0';
	
	PG_RETURN_CSTRING(result);	
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
		PG_RETURN_RDF_TERM(create_term_bool(*term1->text));
  
	// Prefix test
	result = !strncasecmp(term1->text, term2->text, get_text_len(term2));
	PG_RETURN_RDF_TERM(create_term_bool(result));
}
