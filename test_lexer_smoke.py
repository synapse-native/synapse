#!/usr/bin/env python3
"""Smoke test for lexer with ADT tokens"""

from lexer import Lexer

# Read the test file
with open('tests/test_lexer_ADTs.syn', 'r', encoding='utf-8') as f:
    fuente = f.read()

print("Testing lexer with ADT tokens...")
print(f"Source code:\n{fuente}\n")

try:
    lexer = Lexer(fuente)
    tokens = lexer.tokenizar()
    
    print("Tokens generated:")
    for token in tokens:
        print(f"  {token}")
    
    print(f"\nTotal tokens: {len(tokens)}")
    
    # Check for specific tokens
    token_types = [token.tipo for token in tokens]
    print(f"\nToken types: {token_types}")
    
    # Verify MATCH and ARROW_RIGHT tokens are present
    from ast_nodes import TokenID
    match_tokens = [t for t in tokens if t.tipo == TokenID.MATCH]
    arrow_right_tokens = [t for t in tokens if t.tipo == TokenID.ARROW_RIGHT]
    
    print(f"\nMATCH tokens found: {len(match_tokens)}")
    print(f"ARROW_RIGHT tokens found: {len(arrow_right_tokens)}")
    
    if match_tokens and arrow_right_tokens:
        print("\n✅ SUCCESS: Lexer correctly tokenized MATCH and ARROW_RIGHT")
    else:
        print("\n❌ FAILURE: Missing expected tokens")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
