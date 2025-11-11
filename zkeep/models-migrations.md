Models

```ruby

class User < ApplicationRecord
  has_secure_password

  has_many :center_assignments, dependent: :destroy
  has_many :centers, through: :center_assignments

  enum :role, {
    admin: "admin",
    planner: "planner",
    visitor: "visitor"
  }, default: "visitor"

  validates :email, presence: true, uniqueness: true
end
```

```ruby
class Center < ApplicationRecord
  has_many :center_assignments, dependent: :destroy
  has_many :planners, -> { where(role: "planner") }, through: :center_assignments, source: :user
  has_many :users, through: :center_assignments

  has_many :courses, dependent: :destroy
  has_many :gong_sounds, dependent: :destroy
  has_many :devices, dependent: :destroy
  has_one :center_export, dependent: :destroy

  validates :name, presence: true, uniqueness: true
  validates :dhamma_subdomain, presence: true, uniqueness: true
  validates :location_id, presence: true, uniqueness: true
end
```

```ruby
class CenterAssignment < ApplicationRecord
  belongs_to :user
  belongs_to :center

  validates :user_id, uniqueness: { scope: :center_id }
end
```

```ruby
class Course < ApplicationRecord
  belongs_to :center

  validates :course_type, presence: true
  validates :course_start_date, presence: true
  validates :course_end_date, presence: true
  validates :api_course_id, presence: true, uniqueness: { scope: :center_id }

  scope :upcoming, -> { where("course_start_date >= ?", Date.today) }
  scope :for_export, ->(center) { where(center: center).upcoming.order(:course_start_date) }

  # Returns unique course types for a center (these become period_types)
  def self.period_types_for_center(center)
    where(center: center).distinct.pluck(:course_type).sort
  end
end
```

```ruby
class Structure < ApplicationRecord
  self.primary_key = [:course_type, :day_sequence]

  validates :course_type, presence: true
  validates :day_sequence, presence: true, numericality: { only_integer: true, greater_than_or_equal_to: 0 }
  validates :day_type, presence: true

  # Optional: scope to filter by course type
  scope :for_course_type, ->(type) { where(course_type: type) }
end
```

```ruby

class Timing < ApplicationRecord
  self.primary_key = [:course_type, :day_type, :gong_time]

  validates :course_type, presence: true
  validates :day_type, presence: true
  validates :gong_time, presence: true
  validates :gong_sound, presence: true, numericality: { only_integer: true }

  scope :for_course_type, ->(type) { where(course_type: type) }
  scope :for_day_type, ->(type) { where(day_type: type) }
end
```

```ruby
class GongSound < ApplicationRecord
  belongs_to :center
  has_one_attached :wav_file

  validates :gong_sound, presence: true, numericality: { only_integer: true }
  validates :gong_sound, uniqueness: { scope: :center_id }
  validates :num_strikes, presence: true, numericality: { only_integer: true, greater_than: 0 }
  validates :delay_ms, presence: true, numericality: { only_integer: true, greater_than_or_equal_to: 0 }
end
```

```ruby
class Device < ApplicationRecord
  belongs_to :center

  has_secure_token :api_token

  validates :name, presence: true, uniqueness: { scope: :center_id }
  validates :api_token, presence: true, uniqueness: true

  def touch_last_seen!
    update_column(:last_seen_at, Time.current)
  end
end
```

```ruby
class CenterExport < ApplicationRecord
  belongs_to :center

  validates :checksum, presence: true
  validates :exported_at, presence: true

  # Check if export needs regeneration
  def stale?
    # Regenerate if structures, timings, courses, or gong_sounds changed
    latest_change = [
      center.courses.maximum(:updated_at),
      center.gong_sounds.maximum(:updated_at),
      Structure.maximum(:updated_at),
      Timing.maximum(:updated_at)
    ].compact.max

    latest_change.nil? || exported_at.nil? || latest_change > exported_at
  end
end
```


Migrations

```ruby
class CreateUsers < ActiveRecord::Migration[8.0]
  def change
    create_table :users do |t|
      t.string :email, null: false
      t.string :password_digest, null: false
      t.string :role, null: false, default: "visitor"

      t.timestamps
    end

    add_index :users, :email, unique: true
    add_index :users, :role
  end
end
```

```ruby
class CreateCenters < ActiveRecord::Migration[8.0]
  def change
    create_table :centers do |t|
      t.string :name, null: false
      t.string :dhamma_subdomain, null: false
      t.integer :location_id, null: false
      t.string :dhamma_name
      t.string :timezone, default: "UTC"

      t.timestamps
    end

    add_index :centers, :name, unique: true
    add_index :centers, :dhamma_subdomain, unique: true
    add_index :centers, :location_id, unique: true
  end
end
```

```ruby
class CreateCenterAssignments < ActiveRecord::Migration[8.0]
  def change
    create_table :center_assignments do |t|
      t.references :user, null: false, foreign_key: true
      t.references :center, null: false, foreign_key: true

      t.timestamps
    end

    add_index :center_assignments, [:user_id, :center_id], unique: true
  end
end
```

```ruby
class CreateCourses < ActiveRecord::Migration[8.0]
  def change
    create_table :courses do |t|
      t.references :center, null: false, foreign_key: true
      t.integer :api_course_id, null: false
      t.string :course_type, null: false
      t.string :course_type_anchor
      t.date :course_start_date, null: false
      t.date :course_end_date, null: false

      t.timestamps
    end

    add_index :courses, [:center_id, :api_course_id], unique: true
    add_index :courses, [:center_id, :course_start_date]
    add_index :courses, :course_type
  end
end
```

```ruby
class CreateStructures < ActiveRecord::Migration[8.0]
  def change
    create_table :structures, primary_key: [:course_type, :day_sequence] do |t|
      t.string :course_type, null: false
      t.integer :day_sequence, null: false
      t.string :day_type, null: false

      t.timestamps
    end

    add_index :structures, :course_type
    add_index :structures, :day_type
  end
end
```

```ruby

class CreateTimings < ActiveRecord::Migration[8.0]
  def change
    create_table :timings, primary_key: [:course_type, :day_type, :gong_time] do |t|
      t.string :course_type, null: false
      t.string :day_type, null: false
      t.string :gong_time, null: false
      t.integer :gong_sound, null: false
      t.boolean :automatic_gong, null: false, default: true
      t.string :gong_description

      t.timestamps
    end

    add_index :timings, :course_type
    add_index :timings, [:course_type, :day_type]
  end
end
```

```ruby

class CreateGongSounds < ActiveRecord::Migration[8.0]
  def change
    create_table :gong_sounds do |t|
      t.references :center, null: false, foreign_key: true
      t.integer :gong_sound, null: false
      t.integer :num_strikes, null: false
      t.integer :delay_ms, null: false

      t.timestamps
    end

    add_index :gong_sounds, [:center_id, :gong_sound], unique: true
  end
end
```

```ruby
class CreateDevices < ActiveRecord::Migration[8.0]
  def change
    create_table :devices do |t|
      t.references :center, null: false, foreign_key: true
      t.string :name, null: false
      t.string :api_token, null: false
      t.datetime :last_seen_at
      t.string :current_version

      t.timestamps
    end

    add_index :devices, :api_token, unique: true
    add_index :devices, [:center_id, :name], unique: true
  end
end
```

```ruby
class CreateCenterExports < ActiveRecord::Migration[8.0]
  def change
    create_table :center_exports do |t|
      t.references :center, null: false, foreign_key: true
      t.string :checksum, null: false
      t.datetime :exported_at, null: false

      t.timestamps
    end

    add_index :center_exports, :center_id, unique: true
  end
end
```

### Next steps:
1. Run rails active_storage:install for wav file uploads
2. Run rails db:migrate
3. Would you like me to create:
- The sync job to fetch courses from dhamma.org API?
- The export service to build the SQLite file?
- The API controller for Pi polling?
