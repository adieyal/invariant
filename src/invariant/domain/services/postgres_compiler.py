"""PostgresCompiler domain service for compiling logical plans to SQL.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.query.domain.services instead.
"""

# Re-export from new location for backward compatibility
from invariant.query.domain.services.postgres_compiler import (
    CompiledQuery,
    PostgresCompiler,
    PostgresCompilerError,
    _quote_ident,
    compile_time_grain,
)

__all__ = [
    "CompiledQuery",
    "PostgresCompiler",
    "PostgresCompilerError",
    "_quote_ident",
    "compile_time_grain",
]
