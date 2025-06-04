"""Integration tests for category filtering via CLI."""

import pytest
import subprocess
import json
import tempfile
import shutil
from pathlib import Path


class TestCategoryFilteringIntegration:
    """Test category filtering through the CLI interface."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with cli.py for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Copy cli.py to temp directory
        original_cli = Path(__file__).parent.parent / "src" / "momentum" / "cli.py"
        temp_cli = temp_path / "cli.py"
        shutil.copy2(original_cli, temp_cli)

        # Create temp storage file path
        temp_storage = temp_path / "test_storage.json"

        yield temp_path, temp_cli, temp_storage

        # Cleanup
        shutil.rmtree(temp_dir)

    def run_cli(self, temp_cli, temp_storage, command, stdin_input=None):
        """Helper to run CLI commands and return result."""
        # Handle quoted arguments properly for Windows and spaces
        if "--filter" in command:
            # Split command carefully to preserve filter arguments
            parts = [
                "python",
                str(temp_cli),
                "--plain",
                "--store",
                str(temp_storage),
            ]

            # Parse the command manually to handle filters with spaces
            cmd_parts = command.split()
            i = 0
            while i < len(cmd_parts):
                if cmd_parts[i] == "--filter" and i + 1 < len(cmd_parts):
                    parts.append("--filter")
                    # Next part is the filter value - remove quotes if present
                    filter_value = cmd_parts[i + 1]
                    if filter_value.startswith('"') and filter_value.endswith('"'):
                        filter_value = filter_value[1:-1]  # Remove quotes
                    parts.append(filter_value)
                    i += 2
                else:
                    parts.append(cmd_parts[i])
                    i += 1
        else:
            parts = [
                "python",
                str(temp_cli),
                "--plain",
                "--store",
                str(temp_storage),
            ] + command.split()

        # Set environment to handle Unicode properly
        env = {
            **subprocess.os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONLEGACYWINDOWSSTDIO": "1",
            "MOMENTUM_TODAY_KEY": "2025-05-30",
        }

        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            input=stdin_input,
            timeout=10,
            env=env,
        )
        return result

    def load_storage(self, temp_storage):
        """Helper to load and return storage data."""
        if temp_storage.exists():
            return json.loads(temp_storage.read_text(encoding="utf-8"))
        return {}

    def setup_test_data(self, temp_storage):
        """Set up test data with various categories."""
        data = {
            "backlog": [
                {
                    "task": "Work meeting prep @work #low",
                    "categories": ["work"],
                    "tags": ["low"],
                    "ts": "2025-05-30T09:00:00",
                },
                {
                    "task": "Personal project @personal #someday",
                    "categories": ["personal"],
                    "tags": ["someday"],
                    "ts": "2025-05-30T10:00:00",
                },
                {
                    "task": "Client presentation @client @work #urgent",
                    "categories": ["client", "work"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T11:00:00",
                },
                {
                    "task": "Groceries @personal #urgent",
                    "categories": ["personal"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T12:00:00",
                },
                {
                    "task": "No category task #low",
                    "categories": [],
                    "tags": ["low"],
                    "ts": "2025-05-30T13:00:00",
                },
                {
                    "task": "Review design @design #urgent",
                    "categories": ["design"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T13:30:00",
                },
            ],
            "2025-05-30": {
                "todo": {
                    "task": "Active work task @work #important",
                    "categories": ["work"],
                    "tags": ["important"],
                    "ts": "2025-05-30T14:00:00",
                },
                "done": [
                    {
                        "id": "done1",
                        "task": {
                            "task": "Completed work @work #low",
                            "categories": ["work"],
                            "tags": ["low"],
                            "ts": "2025-05-30T08:00:00",
                        },
                        "ts": "2025-05-30T08:30:00",
                    },
                    {
                        "id": "done2",
                        "task": {
                            "task": "Completed personal @personal #urgent",
                            "categories": ["personal"],
                            "tags": ["urgent"],
                            "ts": "2025-05-30T07:00:00",
                        },
                        "ts": "2025-05-30T07:30:00",
                    },
                    {
                        "id": "done3",
                        "task": {
                            "task": "Mixed category done @work @personal #someday",
                            "categories": ["work", "personal"],
                            "tags": ["someday"],
                            "ts": "2025-05-30T06:00:00",
                        },
                        "ts": "2025-05-30T06:30:00",
                    },
                    {
                        "id": "done4",
                        "task": {
                            "task": "Another completed work @work #urgent",
                            "categories": ["work"],
                            "tags": ["urgent"],
                            "ts": "2025-05-30T05:00:00",
                        },
                        "ts": "2025-05-30T05:30:00",
                    },
                ],
            },
        }
        temp_storage.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestStatusFiltering(TestCategoryFilteringIntegration):
    """Test status command with filtering."""

    def test_status_filter_work(self, temp_project_dir):
        """Test status filtering by work category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "status --filter @work")

        assert result.returncode == 0
        assert "(filtered by: @work)" in result.stdout
        assert "Active work task @work #important" in result.stdout
        assert "Completed work @work" in result.stdout
        assert "Mixed category done @work @personal" in result.stdout
        assert "Completed personal @personal" not in result.stdout

    def test_status_filter_personal(self, temp_project_dir):
        """Test status filtering by personal category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "status --filter @personal")

        assert result.returncode == 0
        assert "(filtered by: @personal)" in result.stdout
        assert "Completed personal @personal" in result.stdout
        assert "Mixed category done @work @personal" in result.stdout
        # Filter out debug lines before asserting
        user_lines = [
            line for line in result.stdout.splitlines() if not line.startswith("DEBUG:")
        ]
        user_output = "\n".join(user_lines)
        assert "Active work task @work" not in user_output
        assert "No active task matches filter" in user_output

    def test_status_filter_multiple_categories(self, temp_project_dir):
        """Test status filtering by multiple categories."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "status --filter @work,@personal")

        assert result.returncode == 0
        assert "(filtered by: @work, @personal)" in result.stdout
        assert "Active work task @work" in result.stdout
        assert "Completed work @work" in result.stdout
        assert "Completed personal @personal" in result.stdout
        assert "Mixed category done @work @personal" in result.stdout

    def test_status_filter_nonexistent_category(self, temp_project_dir):
        """Test status filtering by nonexistent category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "status --filter @nonexistent")

        assert result.returncode == 0
        assert "(filtered by: @nonexistent)" in result.stdout
        assert "No active task matches filter" in result.stdout
        assert "No completed tasks match the filter" in result.stdout

    def test_status_no_filter(self, temp_project_dir):
        """Test status without filter shows all tasks."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "status")

        assert result.returncode == 0
        assert "(filtered by:" not in result.stdout
        assert "Active work task @work" in result.stdout
        assert "Completed work @work" in result.stdout
        assert "Completed personal @personal" in result.stdout
        assert "Mixed category done @work @personal" in result.stdout

    def test_status_invalid_filter_format(self, temp_project_dir):
        """Test status with invalid filter format."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        result = self.run_cli(temp_cli, temp_storage, "status --filter work")

        assert result.returncode == 0
        assert (
            "Invalid filter item: 'work'. Must start with @ (category) or # (tag)."
            in result.stdout
        )

    def test_status_filter_tag_urgent(self, temp_project_dir):
        """Test status filtering by #urgent tag."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, 'status --filter "#urgent"')

        assert result.returncode == 0
        assert "(filtered by: #urgent)" in result.stdout
        # Active task is #important, not #urgent
        assert "No active task matches filter" in result.stdout
        assert "Completed personal @personal #urgent" in result.stdout
        assert "Another completed work @work #urgent" in result.stdout
        assert "Completed work @work #low" not in result.stdout

    def test_status_filter_tag_low(self, temp_project_dir):
        """Test status filtering by #low tag."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, 'status --filter "#low"')

        assert result.returncode == 0
        assert "(filtered by: #low)" in result.stdout
        assert "No active task matches filter" in result.stdout
        assert "Completed work @work #low" in result.stdout
        assert "Completed personal @personal #urgent" not in result.stdout

    def test_status_filter_combined_category_tag(self, temp_project_dir):
        """Test status filtering by @work and #urgent."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        # Note: The active task is @work #important, so it should not show up
        result = self.run_cli(temp_cli, temp_storage, 'status --filter "@work,#urgent"')

        assert result.returncode == 0
        assert "(filtered by: @work, #urgent)" in result.stdout
        assert "No active task matches filter" in result.stdout
        assert "Another completed work @work #urgent" in result.stdout  # Matches both
        assert (
            "Completed work @work #low" not in result.stdout
        )  # Matches @work but not #urgent
        assert (
            "Completed personal @personal #urgent" not in result.stdout
        )  # Matches #urgent but not @work


class TestBacklogFiltering(TestCategoryFilteringIntegration):
    """Test backlog list command with filtering."""

    def test_backlog_list_filter_work(self, temp_project_dir):
        """Test backlog list filtering by work category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @work")

        assert result.returncode == 0
        assert "Backlog (filtered by: @work):" in result.stdout
        assert "1. Work meeting prep @work" in result.stdout
        assert "2. Client presentation @client @work #urgent" in result.stdout
        assert "Personal project @personal" not in result.stdout
        assert "Groceries @personal" not in result.stdout
        assert "No category task" not in result.stdout

    def test_backlog_list_filter_personal(self, temp_project_dir):
        """Test backlog list filtering by personal category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @personal")

        assert result.returncode == 0
        assert "Backlog (filtered by: @personal):" in result.stdout
        assert "1. Personal project @personal" in result.stdout
        assert "2. Groceries @personal" in result.stdout
        assert "Work meeting prep @work" not in result.stdout
        assert "Client presentation" not in result.stdout

    def test_backlog_list_filter_client(self, temp_project_dir):
        """Test backlog list filtering by client category."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @client")

        assert result.returncode == 0
        assert "Backlog (filtered by: @client):" in result.stdout
        assert "1. Client presentation @client @work #urgent" in result.stdout
        assert "Work meeting prep" not in result.stdout
        assert "Personal project" not in result.stdout

    def test_backlog_list_filter_multiple_categories(self, temp_project_dir):
        """Test backlog list filtering by multiple categories."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(
            temp_cli, temp_storage, "backlog list --filter @work,@personal"
        )

        assert result.returncode == 0
        assert "Backlog (filtered by: @work, @personal):" in result.stdout
        assert "Work meeting prep @work" in result.stdout
        assert "Personal project @personal" in result.stdout
        assert "Client presentation @client @work" in result.stdout
        assert "Groceries @personal" in result.stdout
        # Should not show uncategorized task
        assert "No category task" not in result.stdout

    def test_backlog_list_no_matches(self, temp_project_dir):
        """Test backlog list when no items match filter."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(
            temp_cli, temp_storage, "backlog list --filter @nonexistent"
        )

        assert result.returncode == 0
        assert "Backlog (filtered by: @nonexistent):" in result.stdout
        assert "No backlog items match the filter." in result.stdout

    def test_backlog_list_no_filter(self, temp_project_dir):
        """Test backlog list without filter shows all items."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, "backlog list")

        assert result.returncode == 0
        assert "Backlog:" in result.stdout
        assert "(filtered by:" not in result.stdout
        assert "Work meeting prep @work" in result.stdout
        assert "Personal project @personal" in result.stdout
        assert "Client presentation @client @work" in result.stdout
        assert "Groceries @personal" in result.stdout
        assert "No category task" in result.stdout

    def test_backlog_list_invalid_filter(self, temp_project_dir):
        """Test backlog list with invalid filter format."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter work")

        assert result.returncode == 0
        assert (
            "Invalid filter item: 'work'. Must start with @ (category) or # (tag)."
            in result.stdout
        )

    def test_backlog_list_filter_tag_urgent(self, temp_project_dir):
        """Test backlog list filtering by #urgent tag."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, 'backlog list --filter "#urgent"')

        assert result.returncode == 0
        assert "(filtered by: #urgent)" in result.stdout
        assert "Client presentation @client @work #urgent" in result.stdout
        assert "Groceries @personal #urgent" in result.stdout
        assert "Review design @design #urgent" in result.stdout
        assert "Work meeting prep @work #low" not in result.stdout
        assert "Personal project @personal #someday" not in result.stdout

    def test_backlog_list_filter_combined(self, temp_project_dir):
        """Test backlog list filtering by @work and #urgent."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(
            temp_cli, temp_storage, 'backlog list --filter "@work,#urgent"'
        )

        assert result.returncode == 0
        assert "(filtered by: @work, #urgent)" in result.stdout
        assert "Client presentation @client @work #urgent" in result.stdout
        assert (
            "Groceries @personal #urgent" not in result.stdout
        )  # Has #urgent but not @work
        assert (
            "Work meeting prep @work #low" not in result.stdout
        )  # Has @work but not #urgent


class TestFilteringWorkflows(TestCategoryFilteringIntegration):
    """Test complete workflows with filtering."""

    def test_add_and_filter_workflow(self, temp_project_dir):
        """Test adding categorized tasks and filtering them."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        # Add work tasks to backlog
        result = self.run_cli(temp_cli, temp_storage, "backlog add Work task 1 @work")
        assert result.returncode == 0

        result = self.run_cli(
            temp_cli, temp_storage, "backlog add Personal task @personal"
        )
        assert result.returncode == 0

        result = self.run_cli(
            temp_cli, temp_storage, "backlog add Mixed task @work @personal"
        )
        assert result.returncode == 0

        # Filter by work category
        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @work")
        assert result.returncode == 0
        assert "Work task 1 @work" in result.stdout
        assert "Mixed task @work @personal" in result.stdout
        assert "Personal task @personal" not in result.stdout

        # Filter by personal category
        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @personal")
        assert result.returncode == 0
        assert "Personal task @personal" in result.stdout
        assert "Mixed task @work @personal" in result.stdout
        assert "Work task 1 @work" not in result.stdout

    def test_complete_and_filter_workflow(self, temp_project_dir):
        """Test completing categorized tasks and filtering status."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        # Add and activate a work task
        result = self.run_cli(temp_cli, temp_storage, "add Work task @work #urgent")
        assert result.returncode == 0

        # Complete the task
        result = self.run_cli(temp_cli, temp_storage, "done", stdin_input="\n")
        assert result.returncode == 0

        # Add a personal task
        result = self.run_cli(temp_cli, temp_storage, "add Personal task @personal")
        assert result.returncode == 0

        # Complete the personal task
        result = self.run_cli(temp_cli, temp_storage, "done", stdin_input="\n")
        assert result.returncode == 0

        # Filter status by work
        result = self.run_cli(temp_cli, temp_storage, "status --filter @work")
        assert result.returncode == 0
        assert "Work task @work #urgent" in result.stdout
        assert "Personal task @personal" not in result.stdout

        # Filter status by personal
        result = self.run_cli(temp_cli, temp_storage, "status --filter @personal")
        assert result.returncode == 0
        assert "Personal task @personal" in result.stdout
        assert "Work task @work" not in result.stdout

    def test_case_insensitive_filtering(self, temp_project_dir):
        """Test that filtering is case-insensitive for categories and tags."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(
            temp_storage
        )  # Uses @work, @personal, #urgent, #low, #someday, #important

        # Test case-insensitive category filtering for status
        result_cat_status = self.run_cli(
            temp_cli, temp_storage, 'status --filter "@WORK"'
        )
        assert result_cat_status.returncode == 0
        assert (
            "(filtered by: @work)" in result_cat_status.stdout
        )  # Output normalized to lowercase
        user_lines = [
            line
            for line in result_cat_status.stdout.splitlines()
            if not line.startswith("DEBUG:")
        ]
        user_output = "\n".join(user_lines)
        assert "Active work task @work #important" in user_output
        assert "Completed work @work #low" in user_output
        assert "Another completed work @work #urgent" in user_output
        assert "Mixed category done @work @personal #someday" in user_output

        # Test case-insensitive tag filtering for status
        result_tag_status = self.run_cli(
            temp_cli, temp_storage, 'status --filter "#URGENT"'
        )
        assert result_tag_status.returncode == 0
        assert "(filtered by: #urgent)" in result_tag_status.stdout  # Output normalized
        user_lines = [
            line
            for line in result_tag_status.stdout.splitlines()
            if not line.startswith("DEBUG:")
        ]
        user_output = "\n".join(user_lines)
        assert "No active task matches filter" in user_output  # Active is #important
        assert "Completed personal @personal #urgent" in user_output
        assert "Another completed work @work #urgent" in user_output

        # Test case-insensitive category filtering for backlog
        result_cat_backlog = self.run_cli(
            temp_cli, temp_storage, 'backlog list --filter "@CLIENT"'
        )
        assert result_cat_backlog.returncode == 0
        assert "(filtered by: @client)" in result_cat_backlog.stdout
        assert "Client presentation @client @work #urgent" in result_cat_backlog.stdout

        # Test case-insensitive tag filtering for backlog
        result_tag_backlog = self.run_cli(
            temp_cli, temp_storage, 'backlog list --filter "#SOMEDAY"'
        )
        assert result_tag_backlog.returncode == 0
        assert "(filtered by: #someday)" in result_tag_backlog.stdout
        assert "Personal project @personal #someday" in result_tag_backlog.stdout

        # Test combined case-insensitive filtering
        result_combined = self.run_cli(
            temp_cli, temp_storage, 'status --filter "@PERSONAL,#URGENT"'
        )
        assert result_combined.returncode == 0
        assert "(filtered by: @personal, #urgent)" in result_combined.stdout
        user_lines = [
            line
            for line in result_combined.stdout.splitlines()
            if not line.startswith("DEBUG:")
        ]
        user_output = "\n".join(user_lines)
        assert "Completed personal @personal #urgent" in user_output
        assert "Active work task @work #important" not in user_output
        assert "Another completed work @work #urgent" not in user_output  # No @personal

    def test_legacy_format_compatibility(self, temp_project_dir):
        """Test filtering with legacy task formats (no explicit category/tag fields)."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        # Manually create legacy format data
        legacy_data = {
            "backlog": [
                {"task": "Legacy work @work", "ts": "2025-05-30T10:00:00"},
                {"task": "Legacy personal @personal", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {
                "todo": "Legacy active @work",
                "done": [
                    {
                        "id": "legacy1",
                        "task": "Legacy completed @personal",
                        "ts": "2025-05-30T09:00:00",
                    }
                ],
            },
        }
        temp_storage.write_text(json.dumps(legacy_data, indent=2), encoding="utf-8")

        # Test backlog filtering
        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @work")
        assert result.returncode == 0
        assert "Legacy work @work" in result.stdout
        assert "Legacy personal @personal" not in result.stdout

        # Test status filtering
        result = self.run_cli(temp_cli, temp_storage, "status --filter @work")
        assert result.returncode == 0
        assert "Legacy active @work" in result.stdout

        result = self.run_cli(temp_cli, temp_storage, "status --filter @personal")
        assert result.returncode == 0
        assert "Legacy completed @personal" in result.stdout
        assert "No active task matches filter" in result.stdout


class TestFilteringErrorHandling(TestCategoryFilteringIntegration):
    """Test error handling in filtering."""

    def test_invalid_category_characters(self, temp_project_dir):
        """Test filtering with invalid category characters."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        # Test with a simpler invalid format that doesn't cause argument parsing issues
        result = self.run_cli(temp_cli, temp_storage, "status --filter @work!")
        assert result.returncode == 0
        assert "Invalid category format" in result.stdout

    def test_empty_category_name(self, temp_project_dir):
        """Test filtering with empty category name."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        result = self.run_cli(temp_cli, temp_storage, "status --filter @")
        assert result.returncode == 0
        assert "Invalid category format" in result.stdout

    def test_special_characters_in_filter(self, temp_project_dir):
        """Test filtering with special characters."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        result = self.run_cli(temp_cli, temp_storage, "backlog list --filter @work!")
        assert result.returncode == 0
        assert "Invalid category format" in result.stdout

    def test_mixed_valid_invalid_categories(self, temp_project_dir):
        """Test filtering with mix of valid and invalid categories."""
        temp_path, temp_cli, temp_storage = temp_project_dir

        result = self.run_cli(temp_cli, temp_storage, "status --filter @work,invalid")
        assert result.returncode == 0
        assert (
            "Invalid filter item: 'invalid'. Must start with @ (category) or # (tag)."
            in result.stdout
        )

    def test_whitespace_handling(self, temp_project_dir):
        """Test filtering with various whitespace scenarios."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        # Test with simple comma-separated categories (our parse_filter_categories handles internal spaces)
        result = self.run_cli(temp_cli, temp_storage, "status --filter @work,@personal")
        assert result.returncode == 0
        assert "(filtered by: @work, @personal)" in result.stdout


class TestCombinedFiltering(TestCategoryFilteringIntegration):
    """Test more complex combined category and tag filtering scenarios."""

    def test_status_filter_multiple_tags(self, temp_project_dir):
        """Test status filtering by multiple tags (#urgent, #low)."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(temp_cli, temp_storage, 'status --filter "#urgent,#low"')

        assert result.returncode == 0
        assert "(filtered by: #urgent, #low)" in result.stdout
        assert "No active task matches filter" in result.stdout  # Active is #important
        assert "Completed personal @personal #urgent" in result.stdout
        assert "Another completed work @work #urgent" in result.stdout
        assert "Completed work @work #low" in result.stdout
        assert "Mixed category done @work @personal #someday" not in result.stdout

    def test_status_filter_multiple_categories_and_tags(self, temp_project_dir):
        """Test status filtering by multiple categories (@work, @personal) and tags (#urgent, #someday)."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        # This filter should only match tasks that have (@work OR @personal) AND (#urgent OR #someday)
        result = self.run_cli(
            temp_cli,
            temp_storage,
            'status --filter "@work,@personal,#urgent,#someday"',
        )

        assert result.returncode == 0
        assert "(filtered by: @work, @personal, #urgent, #someday)" in result.stdout
        assert (
            "No active task matches filter" in result.stdout
        )  # Active is @work #important
        assert (
            "Completed personal @personal #urgent" in result.stdout
        )  # Matches @personal and #urgent
        assert (
            "Another completed work @work #urgent" in result.stdout
        )  # Matches @work and #urgent
        assert (
            "Mixed category done @work @personal #someday" in result.stdout
        )  # Matches @work, @personal, #someday
        assert (
            "Completed work @work #low" not in result.stdout
        )  # Has @work but #low is not in filter

    def test_backlog_list_filter_multiple_tags(self, temp_project_dir):
        """Test backlog list filtering by multiple tags (#urgent, #low)."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(
            temp_cli, temp_storage, 'backlog list --filter "#urgent,#low"'
        )

        assert result.returncode == 0
        assert "(filtered by: #urgent, #low)" in result.stdout
        assert "Client presentation @client @work #urgent" in result.stdout
        assert "Groceries @personal #urgent" in result.stdout
        assert "Review design @design #urgent" in result.stdout
        assert "Work meeting prep @work #low" in result.stdout
        assert "No category task #low" in result.stdout
        assert "Personal project @personal #someday" not in result.stdout

    def test_backlog_list_filter_multiple_categories_and_tags(self, temp_project_dir):
        """Test backlog list filtering by multiple categories (@work, @personal) and tags (#urgent, #someday)."""
        temp_path, temp_cli, temp_storage = temp_project_dir
        self.setup_test_data(temp_storage)

        result = self.run_cli(
            temp_cli,
            temp_storage,
            'backlog list --filter "@work,@personal,#urgent,#someday"',
        )

        assert result.returncode == 0
        assert "(filtered by: @work, @personal, #urgent, #someday)" in result.stdout
        assert (
            "Client presentation @client @work #urgent" in result.stdout
        )  # @work, #urgent
        assert "Groceries @personal #urgent" in result.stdout  # @personal, #urgent
        assert (
            "Personal project @personal #someday" in result.stdout
        )  # @personal, #someday
        assert (
            "Work meeting prep @work #low" not in result.stdout
        )  # @work, but #low not in filter
        assert (
            "Review design @design #urgent" not in result.stdout
        )  # #urgent, but @design not in filter
        assert (
            "No category task #low" not in result.stdout
        )  # #low, but no category match and #low not in filter with category
