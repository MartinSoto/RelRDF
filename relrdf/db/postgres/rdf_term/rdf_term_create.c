
#include "rdf_term.h"

#include "libpq/pqformat.h"

#ifdef PG_MODULE_MAGIC
PG_MODULE_MAGIC;
#endif

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

