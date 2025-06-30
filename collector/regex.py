"""
Padrões regex para identificar sinais de trading
"""

import re
from typing import Pattern, Dict, Any

# Compilar regex patterns uma vez para melhor performance
class RegexPatterns:
    """Padrões regex para identificar sinais de trading."""
    
    def __init__(self):
        # Win 1ª tentativa - suporta ambos formatos: `ASSET` e **WIN em ASSET**
        self.win_1st: Pattern = re.compile(
            r'✅\s*(?:\*\*WIN\s+em\s+([A-Z]+/[A-Z]+)\*\*|WIN\s+em\s*`([A-Z]+/[A-Z]+)`)\s*✅',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Win 2ª tentativa (G1) - suporta ambos formatos
        self.win_2nd: Pattern = re.compile(
            r'✅\s*(?:\*\*WIN\s*\(G1\)\s+em\s+([A-Z]+/[A-Z]+)\*\*|WIN\s*\(G1\)\s+em\s*`([A-Z]+/[A-Z]+)`)\s*✅',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Win 3ª tentativa (G2) - suporta ambos formatos
        self.win_3rd: Pattern = re.compile(
            r'✅\s*(?:\*\*WIN\s*\(G2\)\s+em\s+([A-Z]+/[A-Z]+)\*\*|WIN\s*\(G2\)\s+em\s*`([A-Z]+/[A-Z]+)`)\s*✅',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Loss/Stop após 3 tentativas - suporta ambos formatos
        self.loss: Pattern = re.compile(
            r'❎\s*(?:\*\*STOP\s+em\s+([A-Z]+/[A-Z]+)\*\*|STOP\s+em\s*`([A-Z]+/[A-Z]+)`)\s*❎',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Mapeamento de padrões para resultados
        self.patterns: Dict[str, Dict[str, Any]] = {
            'win_1st': {
                'pattern': self.win_1st,
                'result': 'W',
                'attempt': 1
            },
            'win_2nd': {
                'pattern': self.win_2nd,
                'result': 'W',
                'attempt': 2
            },
            'win_3rd': {
                'pattern': self.win_3rd,
                'result': 'W',
                'attempt': 3
            },
            'loss': {
                'pattern': self.loss,
                'result': 'L',
                'attempt': None
            }
        }
    
    def find_signal(self, text: str) -> tuple[str, int | None, str] | None:
        """
        Procura por sinais no texto da mensagem.
        
        Args:
            text: Texto da mensagem
            
        Returns:
            Tupla (result, attempt, asset) ou None se não encontrar
        """
        if not text:
            return None
        
        # Testar cada padrão
        for pattern_name, pattern_info in self.patterns.items():
            match = pattern_info['pattern'].search(text)
            if match:
                # Pegar o asset do grupo que não é None (formato `ASSET` ou **ASSET**)
                asset = (match.group(1) or match.group(2)).upper()
                result = pattern_info['result']
                attempt = pattern_info['attempt']
                
                return result, attempt, asset
        
        return None
    
    def test_patterns(self) -> None:
        """Testa os padrões regex com exemplos."""
        test_cases = [
            ("✅ WIN em `ADA/USDT` ✅", ('W', 1, 'ADA/USDT')),
            ("✅ WIN (G1) em `BTC/USDT` ✅", ('W', 2, 'BTC/USDT')),
            ("✅ WIN (G2) em `ETH/USDT` ✅", ('W', 3, 'ETH/USDT')),
            ("❎ STOP em `DOT/USDT` ❎", ('L', None, 'DOT/USDT')),
            # Casos com espaços extras
            ("✅  WIN  em  `SOL/USDT`  ✅", ('W', 1, 'SOL/USDT')),
            ("✅  WIN  (G1)  em  `MATIC/USDT`  ✅", ('W', 2, 'MATIC/USDT')),
            # Casos que não devem matchear
            ("Qualquer outra mensagem", None),
            ("", None),
        ]
        
        print("🧪 Testando padrões regex:")
        print("-" * 50)
        
        for text, expected in test_cases:
            result = self.find_signal(text)
            status = "✅" if result == expected else "❌"
            
            print(f"{status} '{text[:30]}...' -> {result}")
            
            if result != expected:
                print(f"   Esperado: {expected}")
                print(f"   Obtido: {result}")
        
        print("-" * 50)


# Instância global para reutilização
patterns = RegexPatterns()

# Função de conveniência
def find_signal(text: str) -> tuple[str, int | None, str] | None:
    """
    Função de conveniência para encontrar sinais em texto.
    
    Args:
        text: Texto da mensagem
        
    Returns:
        Tupla (result, attempt, asset) ou None se não encontrar
    """
    return patterns.find_signal(text)


if __name__ == "__main__":
    # Executar testes quando rodado diretamente
    patterns.test_patterns()
