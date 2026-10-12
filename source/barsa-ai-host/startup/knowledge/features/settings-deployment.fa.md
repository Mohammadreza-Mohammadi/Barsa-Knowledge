# Settings / Configuration / Deployment

## هدف

برای Requirementهایی که «داده کسب‌وکار عادی» نیستند، زود سراغ Entity یا Code نرو. SystemBuilder چند مکانیزم جدا برای context/configuration/deployment دارد.

## Settings / Configuration taxonomy

خانواده‌های شناخته‌شده:

1. MetaSystem SettingsObject
2. User Settings
3. Application Config Definition / Value
4. Global Parameter
5. User Parameter
6. subsystem-specific Settings Entity
7. structured business Settings Entity

Owner contract برای generic setting precedence:

```text
Default → System Settings → User Settings
```

این precedence را خودکار به هر subsystem-specific setting تعمیم نده.

### راهنمای انتخاب

```text
current/runtime context       → Parameter
application/deployment knob   → Config / System Setting
structured/versioned domain cfg → Settings Entity
user-specific override        → User Setting / User Parameter حسب semantics
```

این mapping guideline مبتنی بر evidence است، نه Best Practice مطلق Freeze‌شده برای همه subsystemها.

### Common mistakes

- ساخت Entity عادی برای یک knob ساده runtime/deployment.
- hard-code کردن configuration در Code وقتی Setting/Config موجود است.
- استفاده از User Setting برای business data مشترک.
- فرض اینکه همه Settingها همان persistence/helper عمومی را دارند.

## Deployment / BIX

BIX/.metaexport صرفاً data dump نیست. lifecycle آن می‌تواند شامل این موارد باشد:

```text
ObjectReference selection/dependency expansion
→ metadata structure
→ related data/deleted data
→ ID mapping + embedded ID rewrite
→ schema changes
→ scripts
→ cache/reference rebuild
```

### قواعد مهم

- Import را atomic فرض نکن؛ چندمرحله‌ای و دارای side effectهای schema/data/script/cache است.
- Clone Import identity جدید می‌سازد و continuation/update معمول از source قبلی قابل اتکا نیست.
- version/dependency checks وجود دارند، ولی همه مسیرهای dependency کامل نیستند.
- deployment واقعی ممکن است علاوه بر Metadata به SQL script، DB object و Code dependency وابسته باشد.
- Snapshot/Simulator recovery/preview ابزار عملیاتی هستند؛ تضمین transaction نیستند.

## AI Integration فعلی

دانش Design این حوزه موجود است، ولی general-purpose semantic writer برای تمام Setting/Config/BIX deployment در Integration فعلی وجود ندارد. برای mutation، payload یا lifecycle حدسی نساز؛ `knowledge/support-matrix.fa.md` و Source/Knowledge Pack مرتبط را بررسی کن.

## System Designer settings / item groups

`ShowInWeb`, `ShowInWin`, `DoNotShowSystemTab` Designer state هستند. nullable visibility (`null != false`) باید در Read/Write حفظ شود. SystemItemGroup Designer concept است و Entity assignment باید portable System-scoped reference داشته باشد؛ source/runtime group id reconstruction identity نیست.

