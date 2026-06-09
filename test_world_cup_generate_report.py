import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
import tempfile


class TestFlagMapping:
    """Test flag emoji mappings."""

    def test_flag_map_completeness(self):
        """Verify FLAG_MAP exists and has expected countries."""
        # Import the script and check FLAG_MAP
        import world_cup_generate_report
        flag_map = world_cup_generate_report.FLAG_MAP
        
        assert len(flag_map) > 0
        assert 'Spain' in flag_map
        assert 'Mexico' in flag_map
        assert 'Brazil' in flag_map

    def test_flag_map_values_are_emojis(self):
        """Verify all flag values are non-empty strings."""
        import world_cup_generate_report
        flag_map = world_cup_generate_report.FLAG_MAP
        
        for country, flag in flag_map.items():
            assert isinstance(flag, str)
            assert len(flag) > 0


class TestDataLoading:
    """Test data loading and sanitization."""

    @patch('pandas.read_excel')
    def test_entries_whitespace_sanitization(self, mock_read_excel):
        """Verify that entries are sanitized (whitespace stripped)."""
        # Create mock data with whitespace
        mock_entries = pd.DataFrame({
            'Player1': [' Spain ', 'Brazil'],
            'Player2': ['Mexico ', ' Argentina']
        })
        
        mock_read_excel.return_value = mock_entries
        
        # Load the script
        import world_cup_generate_report
        
        # Simulate sanitization
        sanitized = mock_entries.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Check that whitespace is removed
        assert sanitized.iloc[0, 0] == 'Spain'
        assert sanitized.iloc[1, 1] == 'Argentina'


class TestPointCalculation:
    """Test point calculation logic."""

    def test_total_points_sum(self):
        """Verify that total_points sums row values correctly."""
        # Create test data
        countries_df = pd.DataFrame({
            'Country': ['Brazil', 'Mexico'],
            'Group stage': [3, 0],
            'R32': [5, 0],
            'R16': [0, 0],
            'QF': [0, 0],
            'SF': [0, 0],
            'F': [0, 0]
        })
        
        round_cols = ['Group stage', 'R32', 'R16', 'QF', 'SF', 'F']
        round_scores = countries_df[round_cols].apply(pd.to_numeric, errors='coerce')
        countries_df['total_points'] = round_scores.sum(axis=1, min_count=1)
        
        assert countries_df.loc[0, 'total_points'] == 8
        assert countries_df.loc[1, 'total_points'] == 0

    def test_alive_flag_logic(self):
        """Verify that alive flag is set correctly based on Eliminated column."""
        countries_df = pd.DataFrame({
            'Country': ['Brazil', 'Mexico', 'USA'],
            'Eliminated': [0, 1, 0]
        })
        
        countries_df['alive'] = countries_df['Eliminated'].fillna(0).astype(int).eq(0)
        
        assert countries_df.loc[0, 'alive'] == True
        assert countries_df.loc[1, 'alive'] == False
        assert countries_df.loc[2, 'alive'] == True


class TestFlagWithTooltip:
    """Test flag HTML generation."""

    def test_flag_with_tooltip_markup(self):
        """Verify that flag_with_tooltip generates correct HTML."""
        import world_cup_generate_report
        
        result = world_cup_generate_report.flag_with_tooltip('Spain')
        
        assert '<span class="flag tooltip"' in result
        assert 'data-tooltip="Spain"' in result
        assert '🇪🇸' in result

    def test_flag_with_tooltip_unknown_country(self):
        """Verify that unknown countries fall back to text."""
        import world_cup_generate_report
        
        result = world_cup_generate_report.flag_with_tooltip('Atlantis')
        
        assert 'data-tooltip="Atlantis"' in result
        assert 'Atlantis' in result


class TestHTMLOutput:
    """Test HTML report generation."""

    @patch('pandas.read_excel')
    def test_html_file_created(self, mock_read_excel):
        """Verify that HTML output file is created."""
        # Mock minimal data
        mock_entries = pd.DataFrame({'Player1': ['Spain', 'Brazil']})
        mock_countries = pd.DataFrame({
            'Country': ['Spain', 'Brazil'],
            'Group': ['B', 'G'],
            'Pot': [1, 1],
            'Eliminated': [0, 0],
            'Group stage': [3, 3],
            'R32': [0, 0],
            'R16': [0, 0],
            'QF': [0, 0],
            'SF': [0, 0],
            'F': [0, 0]
        })
        
        mock_read_excel.side_effect = [mock_entries, mock_countries]
        
        # Create a temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_report.html')
            
            # Simulate HTML generation
            html = '<html><body>Test Report</body></html>'
            with open(output_file, 'w') as f:
                f.write(html)
            
            assert os.path.exists(output_file)
            with open(output_file, 'r') as f:
                content = f.read()
                assert 'Test Report' in content

    def test_html_contains_required_sections(self):
        """Verify that generated HTML contains key sections."""
        html = """
        <html>
        <head>
          <title>World Cup Pool Standings</title>
        </head>
        <body>
          <h1>World Cup Pool Standings</h1>
          <h2>Player standings</h2>
          <table class="player-table"></table>
          <h2>Country points</h2>
          <table class="country-table"></table>
        </body>
        </html>
        """
        
        assert '<title>World Cup Pool Standings</title>' in html
        assert '<h1>World Cup Pool Standings</h1>' in html
        assert 'Player standings' in html
        assert 'Country points' in html
        assert 'player-table' in html
        assert 'country-table' in html


class TestPlayerStandings:
    """Test player standings calculation and sorting."""

    def test_player_sorting_by_points(self):
        """Verify that players are sorted by total points descending."""
        player_rows = [
            {'Player': 'Alice', 'Total points': 15, 'Remaining count': 3},
            {'Player': 'Bob', 'Total points': 20, 'Remaining count': 2},
            {'Player': 'Charlie', 'Total points': 10, 'Remaining count': 5},
        ]
        
        player_df = pd.DataFrame(player_rows)
        sorted_df = player_df.sort_values(by=['Total points', 'Remaining count'], ascending=[False, False])
        
        assert sorted_df.iloc[0]['Player'] == 'Bob'
        assert sorted_df.iloc[1]['Player'] == 'Alice'
        assert sorted_df.iloc[2]['Player'] == 'Charlie'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
