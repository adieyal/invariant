"""PostgreSQL compilation utilities for Invariant.

This package provides SQL compilation for PostgreSQL, which is infrastructure
code that should not exist in the kernel domain layer.

The kernel remains database-agnostic; this contrib package translates
logical query plans to PostgreSQL-specific SQL.
"""

from invariant_contrib.postgres.compiler import (
    CompiledQuery,
    PostgresCompiler,
    PostgresCompilerError,
    compile_time_grain,
)

__all__ = [
    "CompiledQuery",
    "PostgresCompiler",
    "PostgresCompilerError",
    "compile_time_grain",
]
