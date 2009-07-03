
MODULE_big = rdf_term
OBJS = rdf_term_create.o rdf_term_compare.o rdf_term_misc.o rdf_term_btree.o btree_gist.o btree_utils_var.o

PG_CONFIG = pg_config
PGXS := $(shell $(PG_CONFIG) --pgxs)
include $(PGXS)

