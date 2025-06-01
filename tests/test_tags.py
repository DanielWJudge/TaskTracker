"""Tests for task categories and tags functionality."""

from momentum.momentum import (
    parse_tags,
    format_task_with_tags,
    validate_tag_format,
    create_task_data,
    validate_task_name,
    Config,
)


class TestParseTagsBasic:
    """Test basic tag parsing functionality."""

    def test_parse_no_tags(self):
        """Test parsing task with no tags."""
        task = "Simple task with no tags"
        text, categories, tags = parse_tags(task)

        assert text == "Simple task with no tags"
        assert categories == []
        assert tags == []

    def test_parse_single_category(self):
        """Test parsing task with single category."""
        task = "Fix login bug @work"
        text, categories, tags = parse_tags(task)

        assert text == "Fix login bug @work"
        assert categories == ["work"]
        assert tags == []

    def test_parse_single_tag(self):
        """Test parsing task with single tag."""
        task = "Important meeting #urgent"
        text, categories, tags = parse_tags(task)

        assert text == "Important meeting #urgent"
        assert categories == []
        assert tags == ["urgent"]

    def test_parse_category_and_tag(self):
        """Test parsing task with both category and tag."""
        task = "Deploy feature @work #urgent"
        text, categories, tags = parse_tags(task)

        assert text == "Deploy feature @work #urgent"
        assert categories == ["work"]
        assert tags == ["urgent"]

    def test_parse_multiple_categories(self):
        """Test parsing task with multiple categories."""
        task = "Schedule meeting @work @client"
        text, categories, tags = parse_tags(task)

        assert text == "Schedule meeting @work @client"
        assert categories == ["work", "client"]
        assert tags == []

    def test_parse_multiple_tags(self):
        """Test parsing task with multiple tags."""
        task = "Research new framework #learning #low #someday"
        text, categories, tags = parse_tags(task)

        assert text == "Research new framework #learning #low #someday"
        assert categories == []
        assert tags == ["learning", "low", "someday"]

    def test_parse_mixed_multiple(self):
        """Test parsing task with multiple categories and tags."""
        task = "Review code @work @team #urgent #review"
        text, categories, tags = parse_tags(task)

        assert text == "Review code @work @team #urgent #review"
        assert categories == ["work", "team"]
        assert tags == ["urgent", "review"]


class TestParseTagsEdgeCases:
    """Test edge cases and special scenarios."""

    def test_parse_tags_at_beginning(self):
        """Test tags at the beginning of task."""
        task = "@work #urgent Fix the bug"
        text, categories, tags = parse_tags(task)

        assert text == "@work #urgent Fix the bug"
        assert categories == ["work"]
        assert tags == ["urgent"]

    def test_parse_tags_mixed_positions(self):
        """Test tags scattered throughout task."""
        task = "Fix @work the login #urgent bug today"
        text, categories, tags = parse_tags(task)

        assert text == "Fix @work the login #urgent bug today"
        assert categories == ["work"]
        assert tags == ["urgent"]

    def test_parse_duplicate_tags(self):
        """Test handling of duplicate tags."""
        task = "Task @work @work #urgent #urgent"
        text, categories, tags = parse_tags(task)

        assert text == "Task @work @work #urgent #urgent"
        # Should deduplicate
        assert categories == ["work"]
        assert tags == ["urgent"]

    def test_parse_case_sensitivity(self):
        """Test case sensitivity in tags."""
        task = "Task @Work @PERSONAL #Urgent #low"
        text, categories, tags = parse_tags(task)

        assert text == "Task @Work @PERSONAL #Urgent #low"
        # Should preserve original case but normalize for storage
        assert categories == ["work", "personal"]  # normalized to lowercase
        assert tags == ["urgent", "low"]  # normalized to lowercase

    def test_parse_tags_with_underscores(self):
        """Test tags with underscores."""
        task = "Task @work_project #high_priority"
        text, categories, tags = parse_tags(task)

        assert text == "Task @work_project #high_priority"
        assert categories == ["work_project"]
        assert tags == ["high_priority"]

    def test_parse_tags_with_numbers(self):
        """Test tags with numbers."""
        task = "Task @project2024 #sprint3"
        text, categories, tags = parse_tags(task)

        assert text == "Task @project2024 #sprint3"
        assert categories == ["project2024"]
        assert tags == ["sprint3"]


class TestParseTagsInvalid:
    """Test invalid tag formats and error handling."""

    def test_parse_empty_category(self):
        """Test handling of empty category @."""
        task = "Task with empty @ category"
        text, categories, tags = parse_tags(task)

        assert text == "Task with empty @ category"
        assert categories == []  # Empty @ should be ignored
        assert tags == []

    def test_parse_empty_tag(self):
        """Test handling of empty tag #."""
        task = "Task with empty # tag"
        text, categories, tags = parse_tags(task)

        assert text == "Task with empty # tag"
        assert categories == []
        assert tags == []  # Empty # should be ignored

    def test_parse_tags_with_spaces(self):
        """Test tags with spaces (invalid format)."""
        task = "Task @work space #urgent task"
        text, categories, tags = parse_tags(task)

        assert text == "Task @work space #urgent task"
        # Should only capture valid parts
        assert categories == ["work"]  # stops at space
        assert tags == ["urgent"]  # stops at space

    def test_parse_special_characters(self):
        """Test tags with special characters."""
        task = "Task @work-project #urgent!"
        text, categories, tags = parse_tags(task)

        assert text == "Task @work-project #urgent!"
        # Hyphens might be allowed, but ! should stop parsing
        assert categories == ["work-project"]
        assert tags == ["urgent"]  # stops at !


class TestValidateTagFormat:
    """Test tag format validation."""

    def test_valid_tag_formats(self):
        """Test valid tag formats."""
        valid_tags = [
            "work",
            "personal",
            "urgent",
            "low_priority",
            "project2024",
            "team-alpha",
        ]
        for tag in valid_tags:
            assert validate_tag_format(tag), f"'{tag}' should be valid"

    def test_invalid_tag_formats(self):
        """Test invalid tag formats."""
        invalid_tags = [
            "",  # empty
            "tag with spaces",
            "tag!",  # special char
            "tag@symbol",  # @ in tag
            "tag#hash",  # # in tag
            "a" * 51,  # too long (assuming 50 char limit)
        ]
        for tag in invalid_tags:
            assert not validate_tag_format(tag), f"'{tag}' should be invalid"


class TestFormatTaskWithTags:
    """Test task display formatting with tag highlighting."""

    def test_format_no_tags_plain_mode(self):
        """Test formatting task with no tags in plain mode."""
        task = "Simple task"
        categories = []
        tags = []

        result = format_task_with_tags(task, categories, tags, plain_mode=True)
        assert result == "Simple task"

    def test_format_with_tags_plain_mode(self):
        """Test formatting task with tags in plain mode."""
        task = "Deploy feature @work #urgent"
        categories = ["work"]
        tags = ["urgent"]

        result = format_task_with_tags(task, categories, tags, plain_mode=True)
        # In plain mode, should show tags without colors
        assert "@work" in result
        assert "#urgent" in result
        assert result == "Deploy feature @work #urgent"

    def test_format_with_tags_color_mode(self):
        """Test formatting task with tags in color mode."""
        task = "Deploy feature @work #urgent"
        categories = ["work"]
        tags = ["urgent"]

        result = format_task_with_tags(task, categories, tags, plain_mode=False)
        # Should contain the original text plus color codes
        assert "Deploy feature" in result
        assert "@work" in result
        assert "#urgent" in result
        # Should have ANSI color codes (we'll implement color logic)
        # assert "\033[" in result  # ANSI escape sequence


class TestTagIntegration:
    """Test integration with existing task storage."""

    def test_create_tagged_task_data(self):
        """Test creating task data structure with tags."""
        task_text = "Fix bug @work #urgent"
        task_data = create_task_data(task_text)

        expected = {
            "task": "Fix bug @work #urgent",
            "categories": ["work"],
            "tags": ["urgent"],
            "ts": task_data["ts"],  # timestamp will be dynamic
        }

        assert task_data["task"] == expected["task"]
        assert task_data["categories"] == expected["categories"]
        assert task_data["tags"] == expected["tags"]
        assert "ts" in task_data

    def test_create_untagged_task_data(self):
        """Test creating task data for untagged task (backward compatibility)."""
        task_text = "Simple task"
        task_data = create_task_data(task_text)

        assert task_data["task"] == "Simple task"
        assert task_data["categories"] == []
        assert task_data["tags"] == []
        assert "ts" in task_data


class TestTaskValidationWithTags:
    """Test task validation including tag validation."""

    def test_validate_tagged_task_valid(self):
        """Test validation of valid tagged task."""
        task = "Deploy feature @work #urgent"
        is_valid, error_msg = validate_task_name(task)
        assert is_valid
        assert error_msg == ""

    def test_validate_tagged_task_too_long(self):
        """Test validation when task + tags exceeds length limit."""
        base_task = "A" * (Config.MAX_TASK_LENGTH - 10)
        task = f"{base_task} @work #urgent #high_priority #important"
        is_valid, error_msg = validate_task_name(task)
        assert not is_valid
        assert "too long" in error_msg

    def test_validate_tagged_task_invalid_tag_format(self):
        """Test validation with invalid tag formats."""
        task = "Task @work space #urgent!"
        is_valid, error_msg = validate_task_name(task)
        assert is_valid or "invalid tag format" in error_msg.lower()


# Test data for property-based testing (advanced)
class TestTagParsingProperties:
    """Property-based tests for tag parsing (advanced learning)."""

    # We'll implement these later with hypothesis library
    def test_parse_tags_reversible(self):
        """Property: parsing tags should be consistent."""
        # Given any valid task with tags
        # When we parse it twice
        # Then we should get the same result
        task = "Deploy @work #urgent"
        result1 = parse_tags(task)
        result2 = parse_tags(task)
        assert result1 == result2

    def test_parse_tags_preserves_text(self):
        """Property: original task text should be preserved."""
        # Given any task text
        # When we parse tags
        # Then the text component should match the original
        task = "Any task @work #urgent text"
        text, categories, tags = parse_tags(task)
        assert text == task


# Learning exercises - implement these as you go!
"""
🎯 LEARNING PROGRESSION:

1. START HERE: Implement parse_tags() to make basic tests pass
2. Add validate_tag_format() for input validation  
3. Create format_task_with_tags() for display
4. Extend create_task_data() to include tag parsing
5. Update validate_task_name() to handle tagged tasks
6. ADVANCED: Add property-based tests with hypothesis

Each step teaches you:
- Test-driven development
- Edge case thinking  
- Input validation patterns
- Display formatting
- Data structure design
- Property-based testing
"""
