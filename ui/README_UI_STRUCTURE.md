
# UI structure

## Common
- `ui/common/` — базовые классы и общие helpers.

## Catalogs
- `ui/catalogs/banks/`
- `ui/catalogs/contagents/`
- `ui/catalogs/contracts/`
- `ui/catalogs/expense_articles/`
- `ui/catalogs/taxes/`
- `ui/catalogs/organization/`

## Documents
- `ui/documents/invoices/`
- `ui/documents/bank/`

## Windows
- `ui/windows/` — сборные окна разделов (`DirectoriesWindow`, `DocumentsWindow`, `ArchiveWindow`).

Для обратной совместимости старые модули в `ui/*.py` оставлены как тонкие wrappers.
