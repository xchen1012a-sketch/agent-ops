"""Unit tests for the shop_db schema loader."""

from __future__ import annotations

from pathlib import Path

from data_query_agent.application.services.data_catalog_service import DataCatalogService
from data_query_agent.application.services.shop_schema_loader import ShopSchemaLoader


def _sql_sample() -> str:
    return """\
-- Table structure for table `dim_channel`
CREATE TABLE `dim_channel` (
  `channel_key` tinyint NOT NULL AUTO_INCREMENT COMMENT '渠道代理键',
  `channel_id` varchar(20) NOT NULL COMMENT '渠道业务编码',
  PRIMARY KEY (`channel_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='渠道维度表';

-- Table structure for table `wide_orders`
CREATE TABLE `wide_orders` (
  `order_id` bigint NOT NULL COMMENT '订单ID',
  `customer_id` varchar(32) NOT NULL COMMENT '客户业务 ID',
  `region` varchar(50) COMMENT '地区',
  `total_amount` decimal(12,2) COMMENT '订单金额',
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单宽表';

-- Table structure for table `dim_customer`
CREATE TABLE `dim_customer` (
  `customer_key` bigint NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`customer_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def _write_sample(tmp_path: Path) -> Path:
    sql_path = tmp_path / "shop_db_export.sql"
    sql_path.write_text(_sql_sample(), encoding="utf-8")
    return sql_path


def _whitelist() -> "object":
    return DataCatalogService().load_sql_whitelist()


def test_loader_returns_only_whitelisted_tables(tmp_path: Path) -> None:
    sql_path = _write_sample(tmp_path)
    loader = ShopSchemaLoader(schema_path=str(sql_path), whitelist=_whitelist())  # type: ignore[arg-type]

    description = loader.load_schema_description()

    assert "CREATE TABLE `wide_orders`" in description
    assert "dim_channel" not in description
    assert "dim_customer" not in description


def test_loader_preserves_column_definitions_and_comments(tmp_path: Path) -> None:
    sql_path = _write_sample(tmp_path)
    loader = ShopSchemaLoader(schema_path=str(sql_path), whitelist=_whitelist())  # type: ignore[arg-type]

    description = loader.load_schema_description()

    assert "`total_amount`" in description
    assert "订单金额" in description
    assert "`customer_id`" in description


def test_loader_returns_empty_when_path_missing(tmp_path: Path) -> None:
    loader = ShopSchemaLoader(
        schema_path=str(tmp_path / "missing.sql"),
        whitelist=_whitelist(),  # type: ignore[arg-type]
    )

    assert loader.load_schema_description() == ""


def test_loader_returns_empty_when_path_blank() -> None:
    loader = ShopSchemaLoader(schema_path="", whitelist=_whitelist())  # type: ignore[arg-type]

    assert loader.load_schema_description() == ""


def test_loader_caches_repeated_calls(tmp_path: Path) -> None:
    sql_path = _write_sample(tmp_path)
    loader = ShopSchemaLoader(schema_path=str(sql_path), whitelist=_whitelist())  # type: ignore[arg-type]

    first = loader.load_schema_description()
    second = loader.load_schema_description()

    assert first is second
