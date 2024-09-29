# supabase_freezed_riverpod_flutter_generator (SFRF)

Help you spin up a relational-database-driven flutter app, powered by Supabase,
Freezed, Riverpod, in no time!

## Download [a latest release of SFRF](https://github.com/01kg/supabase_freezed_riverpod_flutter_generator/releases/latest)

Prepare for later use.

## Start from a skeleton app

It is a good idea to start from a skeleton app that did heavy lifting for you.

```bash
git clone https://github.com/01kg/flutter_skeleton_application_improved.git
```

This skeleton flutter app is based on the "Flutter Skeleton Application"
template. Added support for Freezed, Riverpod, Supabase, DotEnv.

With 4 essential views:

- Home
- Settings
- Login
- Signup

```bash
cd flutter_skeleton_application_improved

# install packages
dart pub get
```

## Connect to your Supabase

```bash
cp .env.example .env

cat .env

# Output:
# SUPABASE_URL=https://YOUR.SUPABASE.URL
# SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

Replace the credentials with your own Supabase's.

## Test flight

```bash
flutter run
```

Signup/Login a Supabase user account, change to dark theme in settings to make
sure the app runs good.

If the skeleton app runs good, then let's generate files based on SQL CREATE
statement.

## Sample SQL CREATE statements

```sql
create table countries (
  id bigint generated by default as identity primary key,
  name varchar,
  description varchar,
  user_id uuid references auth.users on delete cascade on update cascade
);

create table cities (
  id bigint generated by default as identity primary key,
  name varchar,
  description varchar,
  population bigint,
  established_date date,
  area real,
  introduction text,
  longitude double precision,
  lantitude double precision,
  country_id bigint references countries on delete cascade on update cascade,
  user_id uuid references auth.users on delete cascade on update cascade
);


-- If you want to turn on RLS to restrict access:

alter table "countries" enable row level security;

create policy "Authenticated can view own country."
on countries for select
to authenticated
using ( (select auth.uid()) = user_id );

create policy "Authenticated can create own country."
on countries for insert
to authenticated
with check ( (select auth.uid()) = user_id ); 

create policy "Authenticated can update own country."
on countries for update
to authenticated
using ( (select auth.uid()) = user_id )
with check ( (select auth.uid()) = user_id ); 

create policy "Authenticated can delete own country."
on countries for delete
to authenticated
using ( (select auth.uid()) = user_id );




alter table "cities" enable row level security;

create policy "Authenticated can view own city."
on cities for select
to authenticated
using ( (select auth.uid()) = user_id );

create policy "Authenticated can create own city."
on cities for insert
to authenticated
with check ( (select auth.uid()) = user_id ); 

create policy "Authenticated can update own city."
on cities for update
to authenticated
using ( (select auth.uid()) = user_id )
with check ( (select auth.uid()) = user_id ); 

create policy "Authenticated can delete own city."
on cities for delete
to authenticated
using ( (select auth.uid()) = user_id );
```

We created two tables, `countries` and `cities`. Here are something worth noting
(some best practices):

- Every table should have `id` column as the Primary Key.
  - Essential for being referenced.
  - Use `bigint` to be more readable.
  - use `generated by default` to let database decide how to create it.
    ([`generated always` would block UPSERT operations](https://github.com/orgs/supabase/discussions/2837))
  - use `as identity` to make it auto increment.
  - use `primary key` make it able to add relationships with other tables

- `user_id` columns is good for RLS access policy doing restrictions.
  `references auth.users on delete cascade on update cascade` is a good
  practice.
- cities table has a field refers to countries. The field name should be
  `country_id`, not `country`. Because in database, this field is acctually the
  id of a row of countries table. SFRF uses `_id` to identify these fields and
  create a related query and a dropdown list.
- Use `varchar` for short content text. E.g. `name`, `description`. This is good
  for indexing. SFRF would create a one-line height TextFormField for it.
- Use `text` for reaaaaaaaaally long text. E.g. `notes`, `post_content`. SFRF
  would create a 2-8 lines height TextFormField for it.
- Use `date` for date. SFRF would create a date picker for it.
- Use `real` for 6 digits float, and use `double` precision for 15 digits float,
  use `numeric` for n digits float.
- Use snake_case for multi-words field name. E.g. `country_id`. SFRF has
  built-in methods to convert to camelCase, CapCamelCase, Title Case.

The SQL statment script above has two usage:

1. Input it in Supabase's SQL Editor to create tables and policies.
2. SFRF generates all files based on it.

## How SFRF work?

1. Reads `lib/sqls` folder for `.sql` files.
2. Parse `create table ... ;` part to get all the fields (table columns) and
   types
3. Go to/Create `lib/models` folder, put generated Freezed annotated files in
   it.
4. Go to/Create `lib/providers` folder, put generated Riverpod annotated files
   in it.
5. Go to/Create `lib/views` folder, put generated view files in it.

## Step 1: Go to Supabase SQL Editor to create the tables

Copy and paste the SQL statements to in it and run. Make sure no error returned.

You can go to Database -> Schema Visualizer to check the tables' relationships.

![the-relationships](https://github.com/user-attachments/assets/24aeea7e-489a-487f-8ecd-7ef3b7e9854c)

## Step 2: Go to/Create `sqls` folder under `lib` of your Flutter project.

## Step 3: Create a `.sql` file with any name in `sqls` folder, and paste the SQL statements content into it.

## Step 4: Under SFRF's root directory, run `python main.py "THE/PATH/TO/FLUTTER/APP/ROOT/DIRECTORY"`

Thus, all files are generated.

## Step 5: Format all files

The generated files might not match Dart's format standard, it is recommend to
format them for better experience for later editing.

Since by the time of writing, `dart format`
[doesn't recurse through subdirectories](https://dart.dev/tools/dart-format#specify-one-path),
and does not recognize common seen auto-generated files like '\*.g.dart' or
'\*.freezed.dart', so it is necessary to write a command to do so.

```powershell
# Windows PowerShell
Get-ChildItem -Recurse -Filter *.dart | Where-Object { $_.Name -notlike '*.g.dart' -and $_.Name -notlike '*.freezed.dart' } | ForEach-Object { dart format $_.FullName }
```

```sh
Unix/Linux/macOS
find . -name "*.dart" ! -name "*.g.dart" ! -name "*.freezed.dart" -exec flutter format {} \;
```

## Step 6: Under Flutter app's root directory, run `dart run build_runner build`.

This command let Freezed and Riverpod to generate their own codes.

If encounter warning:

```
Found 4 declared outputs which already exist on disk. 
This is likely because the`.dart_tool/build` folder was 
deleted, or you are submitting generated files to your 
source repository.

Delete these files?
1 - Delete
2 - Cancel build
3 - List conflicts
```

Unless you have deep concerns about this, or just select 1 to delete these old
files.

## Step 7: connect the generated views with Flutter app:

Add new views to `onGeneratedRoute` configuration:

```dart
// app.dart

...
      onGenerateRoute: (RouteSettings routeSettings) {
        return MaterialPageRoute<void>(
          settings: routeSettings,
          builder: (BuildContext context) {

            final user = ref.watch(supabaseAuthProvider);

            if (user == null) {
            // if (authEvent.value?.event != AuthChangeEvent.signedIn) {
              if (routeSettings.name == SignupView.routeName) {
                return const SignupView();
              }
              return const LoginView();
            } else {
              switch (routeSettings.name) {
                case SettingsView.routeName:
                  return const SettingsView();
                case SignupView.routeName:
                  return const SignupView();
                case CountriesView.routeName:
                  return const CountriesView(); 
                case CitiesView.routeName:
                  return const CitiesView();
                default:
                  return const HomeView();
              }
            }
          },
        );
      },
...
```

Link views to Settings page:

```dart
// views/settings_view.dart

...
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DropdownButton<ThemeMode>(
                ...
            ),
            const Divider(),
            ListTile(
              title: const Text('Countries'),
              trailing: const Icon(Icons.arrow_forward_ios),
              onTap: () {
                // go to investment projects view
                Navigator.restorablePushNamed(context, CountriesView.routeName);
              },
            ),
            const Divider(),
            ListTile(
              title: const Text('Cities'),
              trailing: const Icon(Icons.arrow_forward_ios),
              onTap: () {
                // go to investment projects view
                Navigator.restorablePushNamed(context, CitiesView.routeName);
              },
            ),
          ],
        ),
      ),
...
```

## Step 8: Modify as you wish

After SFRF did heavy lifting things, it your turn, modify as you like.

At least there are 2 places for you to do something:

1. The list view. Since SFRF can not predict what fields are available for
   displaying in ListTile, so it leave it to a default text:

   ![msedge_8oXSqBuMCV](https://github.com/user-attachments/assets/fbc118e8-8780-405d-abe1-28543100bd89)

1. The dropdown lists. Due to the same reason, you should modify them to display
   correct info:

   ![msedge_9Q5Rn3RrSE](https://github.com/user-attachments/assets/300be4fb-9535-4ed6-ba08-ec05c6ef2d78)

# Thanks for reading!
