import pytest

import archivemymail

class TestConfig:

    @classmethod
    def setup(self):
        self.Config = archivemymail.Config()

    def test_defaults(self):
        assert len(self.Config) == 0

    def test_mapping_properties(self):
        initial_size = len(self.Config)

        # Add
        self.Config["new_entry"] = 1
        assert len(self.Config) == initial_size + 1
        assert self.Config["new_entry"] == 1

        # Modify
        self.Config["new_entry"] = 2
        assert len(self.Config) == initial_size + 1
        assert self.Config["new_entry"] == 2

        # Delete
        del self.Config["new_entry"]
        assert len(self.Config) == initial_size
        assert "new_entry" not in self.Config

        # Iter
        for k in self.Config:
            assert k in self.Config

        # SetDefault
        assert "other key" not in self.Config
        assert self.Config.setdefault("other key", False) == False
        assert self.Config["other key"] is False
        self.Config["other key"] = True
        assert self.Config.setdefault("other key", False) == True
