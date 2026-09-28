# tests/test_runtime_and_system_api.py - 客户运行时环境、私有依赖定位与系统接口测试

import os
import sys
import unittest
import json
import tempfile
import shutil

from xuanjian.runtime_env import (
    get_data_dir,
    get_default_db_path,
    get_node_bin_path,
    get_worker_bundle_path,
    get_frontend_dist_dir,
    get_desensitized_diagnostics,
    is_bundled_node
)
from backend.server import XuanJianAPIHandler


class TestRuntimeEnv(unittest.TestCase):

    def test_get_data_dir_default_and_env_override(self):
        """测试数据目录默认与环境变量覆盖"""
        orig_data_dir = os.environ.get("XUANJIAN_DATA_DIR")
        orig_app_mode = os.environ.get("XUANJIAN_APP_MODE")
        try:
            # 1. 显式覆盖
            with tempfile.TemporaryDirectory() as td:
                os.environ["XUANJIAN_DATA_DIR"] = td
                self.assertEqual(get_data_dir(), os.path.abspath(td))
                self.assertEqual(get_default_db_path(), os.path.join(os.path.abspath(td), "xuanjian.db"))

            # 2. App 模式 (~/Library/Application Support/XuanJian)
            os.environ.pop("XUANJIAN_DATA_DIR", None)
            os.environ["XUANJIAN_APP_MODE"] = "1"
            expected_mac_dir = os.path.abspath(os.path.expanduser("~/Library/Application Support/XuanJian"))
            self.assertEqual(get_data_dir(), expected_mac_dir)

            # 3. 默认源码开发模式
            os.environ.pop("XUANJIAN_APP_MODE", None)
            default_dir = get_data_dir()
            self.assertTrue(default_dir.endswith("data"))
        finally:
            if orig_data_dir is not None:
                os.environ["XUANJIAN_DATA_DIR"] = orig_data_dir
            else:
                os.environ.pop("XUANJIAN_DATA_DIR", None)
            if orig_app_mode is not None:
                os.environ["XUANJIAN_APP_MODE"] = orig_app_mode
            else:
                os.environ.pop("XUANJIAN_APP_MODE", None)

    def test_node_and_worker_path_resolution(self):
        """测试 Node 可执行文件与计算 bundle 路径解析"""
        node_bin = get_node_bin_path()
        self.assertTrue(bool(node_bin))

        worker_path = get_worker_bundle_path()
        self.assertTrue(os.path.isfile(worker_path), f"Worker bundle 未找到: {worker_path}")
        self.assertTrue(worker_path.endswith("calc_worker.bundle.js"))

        dist_path = get_frontend_dist_dir()
        self.assertTrue(os.path.isdir(dist_path), f"前端产物未找到: {dist_path}")

    def test_desensitized_diagnostics(self):
        """测试诊断信息严格脱敏，不含敏感文本、密钥或真实生辰"""
        extra = {
            "records_count": 42,
            "db_integrity": "ok",
            "port": 8788,
            "sensitive_secret_should_not_pass": "sk-1234567890",
            "sensitive_birth": "1990-05-15 14:00"
        }
        diag = get_desensitized_diagnostics(extra)
        diag_json = json.dumps(diag, ensure_ascii=False)

        # 验证核心公开信息
        self.assertEqual(diag["app_version"], "3.0.1")
        self.assertEqual(diag["records_count"], 42)
        self.assertEqual(diag["db_integrity"], "ok")
        self.assertIn("zhouyi", diag["engines"])
        self.assertIn("ziwei", diag["engines"])
        self.assertIn("qimen", diag["engines"])

        # 严格断言绝无敏感数据透传
        self.assertNotIn("sk-1234567890", diag_json)
        self.assertNotIn("1990-05-15", diag_json)
        self.assertNotIn("sensitive_secret_should_not_pass", diag)
        self.assertNotIn("sensitive_birth", diag)


if __name__ == "__main__":
    unittest.main()
