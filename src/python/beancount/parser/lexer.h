#ifndef yyHEADER_H
#define yyHEADER_H 1
#define yyIN_HEADER 1

#line 6 "src/python/beancount/parser/lexer.h"
#line 23 "src/python/beancount/parser/lexer.l"

/* Includes. */
#include <math.h>
#include <stdlib.h>

#include "parser.h"
#include "grammar.h"


/* Build and accumulate an error on the builder object. */
void build_lexer_error(const char* string, size_t length);

/* Build and accumulate an error on the builder object using the current
 * exception state. */
void build_lexer_error_from_exception(void);



/* Callback call site with error handling. */
#define BUILD_LEX(method_name, format, ...)                                             \
    yylval->pyobj = PyObject_CallMethod(builder, method_name, format, __VA_ARGS__);     \
    /* Handle a Python exception raised by the handler {3cfb2739349a} */                \
    if (yylval->pyobj == NULL) {                                                        \
       build_lexer_error_from_exception();                                              \
       return LEX_ERROR;                                                                \
    }                                                                                   \
    /* Lexer builder methods should never return None, check for it. */                 \
    else if (yylval->pyobj == Py_None) {                                                \
        Py_DECREF(Py_None);                                                             \
        build_lexer_error("Unexpected None result from lexer", 34);                     \
        return LEX_ERROR;                                                               \
    }


/* Initialization/finalization methods. These are separate from the yylex_init()
 * and yylex_destroy() and they call them. */
void yylex_initialize(const char* filename, const char* encoding);
void yylex_finalize(void);


/* Global declarations; defined below. */
extern int yy_eof_times;
extern const char* yy_filename;
extern int yycolumn;
extern const char* yy_encoding;

/* String buffer statics. */
extern size_t strbuf_size; /* Current buffer size (not including final nul). */
extern char* strbuf;       /* Current buffer head. */
extern char* strbuf_end;   /* Current buffer sentinel (points to the final nul). */
extern char* strbuf_ptr;   /* Current insertion point in buffer. */
void strbuf_realloc(size_t num_new_chars);



/* Handle detecting the beginning of line. */
extern int yy_line_tokens; /* Number of tokens since the bol. */

#define YY_USER_ACTION  {                               \
    yy_line_tokens++;                                   \
    yylloc->first_line = yylloc->last_line = yylineno;  \
    yylloc->first_column = yycolumn;                    \
    yylloc->last_column = yycolumn+yyleng-1;            \
    yycolumn += yyleng;                                 \
  }


/* Skip the rest of the input line. */
int yy_skip_line(void);


/* Utility functions. */
int strtonl(const char* buf, size_t nchars);


/* Append characters to the static string buffer and verify. */
#define SAFE_COPY_CHAR(value)                    \
	if (strbuf_ptr >= strbuf_end) {         \
            strbuf_realloc(1);                  \
	}                                       \
        *strbuf_ptr++ = value;




#line 93 "src/python/beancount/parser/lexer.h"

#define  YY_INT_ALIGNED short int

/* A lexical scanner generated by flex */

#define FLEX_SCANNER
#define YY_FLEX_MAJOR_VERSION 2
#define YY_FLEX_MINOR_VERSION 5
#define YY_FLEX_SUBMINOR_VERSION 39
#if YY_FLEX_SUBMINOR_VERSION > 0
#define FLEX_BETA
#endif

/* First, we deal with  platform-specific or compiler-specific issues. */

/* begin standard C headers. */
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>

/* end standard C headers. */

/* flex integer type definitions */

#ifndef FLEXINT_H
#define FLEXINT_H

/* C99 systems have <inttypes.h>. Non-C99 systems may or may not. */

#if defined (__STDC_VERSION__) && __STDC_VERSION__ >= 199901L

/* C99 says to define __STDC_LIMIT_MACROS before including stdint.h,
 * if you want the limit (max/min) macros for int types. 
 */
#ifndef __STDC_LIMIT_MACROS
#define __STDC_LIMIT_MACROS 1
#endif

#include <inttypes.h>
typedef int8_t flex_int8_t;
typedef uint8_t flex_uint8_t;
typedef int16_t flex_int16_t;
typedef uint16_t flex_uint16_t;
typedef int32_t flex_int32_t;
typedef uint32_t flex_uint32_t;
#else
typedef signed char flex_int8_t;
typedef short int flex_int16_t;
typedef int flex_int32_t;
typedef unsigned char flex_uint8_t; 
typedef unsigned short int flex_uint16_t;
typedef unsigned int flex_uint32_t;

/* Limits of integral types. */
#ifndef INT8_MIN
#define INT8_MIN               (-128)
#endif
#ifndef INT16_MIN
#define INT16_MIN              (-32767-1)
#endif
#ifndef INT32_MIN
#define INT32_MIN              (-2147483647-1)
#endif
#ifndef INT8_MAX
#define INT8_MAX               (127)
#endif
#ifndef INT16_MAX
#define INT16_MAX              (32767)
#endif
#ifndef INT32_MAX
#define INT32_MAX              (2147483647)
#endif
#ifndef UINT8_MAX
#define UINT8_MAX              (255U)
#endif
#ifndef UINT16_MAX
#define UINT16_MAX             (65535U)
#endif
#ifndef UINT32_MAX
#define UINT32_MAX             (4294967295U)
#endif

#endif /* ! C99 */

#endif /* ! FLEXINT_H */

#ifdef __cplusplus

/* The "const" storage-class-modifier is valid. */
#define YY_USE_CONST

#else	/* ! __cplusplus */

/* C99 requires __STDC__ to be defined as 1. */
#if defined (__STDC__)

#define YY_USE_CONST

#endif	/* defined (__STDC__) */
#endif	/* ! __cplusplus */

#ifdef YY_USE_CONST
#define yyconst const
#else
#define yyconst
#endif

/* Size of default input buffer. */
#ifndef YY_BUF_SIZE
#define YY_BUF_SIZE 16384
#endif

#ifndef YY_TYPEDEF_YY_BUFFER_STATE
#define YY_TYPEDEF_YY_BUFFER_STATE
typedef struct yy_buffer_state *YY_BUFFER_STATE;
#endif

#ifndef YY_TYPEDEF_YY_SIZE_T
#define YY_TYPEDEF_YY_SIZE_T
typedef size_t yy_size_t;
#endif

extern yy_size_t yyleng;

extern FILE *yyin, *yyout;

#ifndef YY_STRUCT_YY_BUFFER_STATE
#define YY_STRUCT_YY_BUFFER_STATE
struct yy_buffer_state
	{
	FILE *yy_input_file;

	char *yy_ch_buf;		/* input buffer */
	char *yy_buf_pos;		/* current position in input buffer */

	/* Size of input buffer in bytes, not including room for EOB
	 * characters.
	 */
	yy_size_t yy_buf_size;

	/* Number of characters read into yy_ch_buf, not including EOB
	 * characters.
	 */
	yy_size_t yy_n_chars;

	/* Whether we "own" the buffer - i.e., we know we created it,
	 * and can realloc() it to grow it, and should free() it to
	 * delete it.
	 */
	int yy_is_our_buffer;

	/* Whether this is an "interactive" input source; if so, and
	 * if we're using stdio for input, then we want to use getc()
	 * instead of fread(), to make sure we stop fetching input after
	 * each newline.
	 */
	int yy_is_interactive;

	/* Whether we're considered to be at the beginning of a line.
	 * If so, '^' rules will be active on the next match, otherwise
	 * not.
	 */
	int yy_at_bol;

    int yy_bs_lineno; /**< The line count. */
    int yy_bs_column; /**< The column count. */
    
	/* Whether to try to fill the input buffer when we reach the
	 * end of it.
	 */
	int yy_fill_buffer;

	int yy_buffer_status;

	};
#endif /* !YY_STRUCT_YY_BUFFER_STATE */

void yyrestart (FILE *input_file  );
void yy_switch_to_buffer (YY_BUFFER_STATE new_buffer  );
YY_BUFFER_STATE yy_create_buffer (FILE *file,int size  );
void yy_delete_buffer (YY_BUFFER_STATE b  );
void yy_flush_buffer (YY_BUFFER_STATE b  );
void yypush_buffer_state (YY_BUFFER_STATE new_buffer  );
void yypop_buffer_state (void );

YY_BUFFER_STATE yy_scan_buffer (char *base,yy_size_t size  );
YY_BUFFER_STATE yy_scan_string (yyconst char *yy_str  );
YY_BUFFER_STATE yy_scan_bytes (yyconst char *bytes,yy_size_t len  );

void *yyalloc (yy_size_t  );
void *yyrealloc (void *,yy_size_t  );
void yyfree (void *  );

/* Begin user sect3 */

#define yywrap() 1
#define YY_SKIP_YYWRAP

extern int yylineno;

extern char *yytext;
#define yytext_ptr yytext

#ifdef YY_HEADER_EXPORT_START_CONDITIONS
#define INITIAL 0
#define INVALID 1
#define STRLIT 2

#endif

#ifndef YY_NO_UNISTD_H
/* Special case for "unistd.h", since it is non-ANSI. We include it way
 * down here because we want the user's section 1 to have been scanned first.
 * The user has a chance to override it with an option.
 */
#include <unistd.h>
#endif

#ifndef YY_EXTRA_TYPE
#define YY_EXTRA_TYPE void *
#endif

/* Accessor methods to globals.
   These are made visible to non-reentrant scanners for convenience. */

int yylex_destroy (void );

int yyget_debug (void );

void yyset_debug (int debug_flag  );

YY_EXTRA_TYPE yyget_extra (void );

void yyset_extra (YY_EXTRA_TYPE user_defined  );

FILE *yyget_in (void );

void yyset_in  (FILE * in_str  );

FILE *yyget_out (void );

void yyset_out  (FILE * out_str  );

yy_size_t yyget_leng (void );

char *yyget_text (void );

int yyget_lineno (void );

void yyset_lineno (int line_number  );

YYSTYPE * yyget_lval (void );

void yyset_lval (YYSTYPE * yylval_param  );

       YYLTYPE *yyget_lloc (void );
    
        void yyset_lloc (YYLTYPE * yylloc_param  );
    
/* Macros after this point can all be overridden by user definitions in
 * section 1.
 */

#ifndef YY_SKIP_YYWRAP
#ifdef __cplusplus
extern "C" int yywrap (void );
#else
extern int yywrap (void );
#endif
#endif

#ifndef yytext_ptr
static void yy_flex_strncpy (char *,yyconst char *,int );
#endif

#ifdef YY_NEED_STRLEN
static int yy_flex_strlen (yyconst char * );
#endif

#ifndef YY_NO_INPUT

#endif

/* Amount of stuff to slurp up with each read. */
#ifndef YY_READ_BUF_SIZE
#define YY_READ_BUF_SIZE 8192
#endif

/* Number of entries by which start-condition stack grows. */
#ifndef YY_START_STACK_INCR
#define YY_START_STACK_INCR 25
#endif

/* Default declaration of generated scanner - a define so the user can
 * easily add parameters.
 */
#ifndef YY_DECL
#define YY_DECL_IS_OURS 1

extern int yylex \
               (YYSTYPE * yylval_param,YYLTYPE * yylloc_param );

#define YY_DECL int yylex \
               (YYSTYPE * yylval_param, YYLTYPE * yylloc_param )
#endif /* !YY_DECL */

/* yy_get_previous_state - get the state just before the EOB char was reached */

#undef YY_NEW_FILE
#undef YY_FLUSH_BUFFER
#undef yy_set_bol
#undef yy_new_buffer
#undef yy_set_interactive
#undef YY_DO_BEFORE_ACTION

#ifdef YY_DECL_IS_OURS
#undef YY_DECL_IS_OURS
#undef YY_DECL
#endif

#line 362 "src/python/beancount/parser/lexer.l"


#line 418 "src/python/beancount/parser/lexer.h"
#undef yyIN_HEADER
#endif /* yyHEADER_H */
