# PsySuite Device Identification System - Technical Design

## Overview

This document describes the technical implementation of the device identification system for PsySuite Android app, ensuring each installation can be uniquely tracked across app updates and reinstallations.

## Requirements Summary

- **First Launch**: Show registration dialog for device ID
- **Persistence**: Survive app updates and reinstallations  
- **Data Tracking**: Include device ID in all uploaded experiments
- **Management**: Allow users to view/change device ID
- **Web Integration**: Display and filter by device ID in web interface

## Technical Implementation

### 1. Android App Implementation

#### 1.1 Storage Strategy

**Primary Storage: SharedPreferences**
```kotlin
class DeviceIdentificationManager private constructor(private val context: Context) {
    
    companion object {
        private const val PREFS_NAME = "psysuite_device_config"
        private const val KEY_DEVICE_ID = "device_identifier"
        private const val KEY_REGISTRATION_DATE = "registration_date"
        private const val KEY_IS_REGISTERED = "is_registered"
        private const val KEY_REGISTRATION_SKIPPED = "registration_skipped"
        private const val KEY_FIRST_LAUNCH_HANDLED = "first_launch_handled"
        
        @Volatile
        private var INSTANCE: DeviceIdentificationManager? = null
        
        fun getInstance(context: Context): DeviceIdentificationManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: DeviceIdentificationManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }
    
    private val sharedPrefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    fun isDeviceRegistered(): Boolean {
        return sharedPrefs.getBoolean(KEY_IS_REGISTERED, false) && 
               !getDeviceId().isNullOrEmpty()
    }
    
    fun isFirstLaunch(): Boolean {
        return !sharedPrefs.getBoolean(KEY_FIRST_LAUNCH_HANDLED, false)
    }
    
    fun isRegistrationSkipped(): Boolean {
        return sharedPrefs.getBoolean(KEY_REGISTRATION_SKIPPED, false)
    }
    
    fun shouldShowRegistrationDialog(): Boolean {
        return isFirstLaunch() || (!isDeviceRegistered() && !isRegistrationSkipped())
    }
    
    fun getDeviceId(): String? {
        return sharedPrefs.getString(KEY_DEVICE_ID, null)
    }
    
    fun setDeviceId(deviceId: String): Boolean {
        if (deviceId.isBlank()) return false
        
        return sharedPrefs.edit()
            .putString(KEY_DEVICE_ID, deviceId.trim())
            .putBoolean(KEY_IS_REGISTERED, true)
            .putBoolean(KEY_FIRST_LAUNCH_HANDLED, true)
            .putBoolean(KEY_REGISTRATION_SKIPPED, false) // Clear skip flag if user registers
            .putLong(KEY_REGISTRATION_DATE, System.currentTimeMillis())
            .commit()
    }
    
    fun skipRegistration() {
        sharedPrefs.edit()
            .putBoolean(KEY_REGISTRATION_SKIPPED, true)
            .putBoolean(KEY_FIRST_LAUNCH_HANDLED, true)
            .putBoolean(KEY_IS_REGISTERED, false)
            .apply()
    }
    
    fun getRegistrationDate(): Long {
        return sharedPrefs.getLong(KEY_REGISTRATION_DATE, 0)
    }
    
    fun clearRegistration() {
        sharedPrefs.edit()
            .remove(KEY_DEVICE_ID)
            .putBoolean(KEY_IS_REGISTERED, false)
            .putBoolean(KEY_REGISTRATION_SKIPPED, false)
            .remove(KEY_REGISTRATION_DATE)
            .apply()
    }
    
    fun getRegistrationStatus(): String {
        return when {
            isDeviceRegistered() -> "Registered: ${getDeviceId()}"
            isRegistrationSkipped() -> "Registration skipped"
            else -> "Not registered"
        }
    }
}
```

**Backup Storage: Internal File**
```kotlin
class DeviceIdBackupManager(private val context: Context) {
    
    private val backupFile = File(context.filesDir, ".psysuite_device_backup")
    
    fun backupDeviceId(deviceId: String) {
        try {
            backupFile.writeText(deviceId)
        } catch (e: Exception) {
            Log.e("DeviceIdBackup", "Failed to backup device ID", e)
        }
    }
    
    fun restoreDeviceId(): String? {
        return try {
            if (backupFile.exists()) {
                backupFile.readText().trim().takeIf { it.isNotEmpty() }
            } else null
        } catch (e: Exception) {
            Log.e("DeviceIdBackup", "Failed to restore device ID", e)
            null
        }
    }
}
```

#### 1.2 Registration Dialog

```kotlin
class DeviceRegistrationDialog : DialogFragment() {
    
    interface OnDeviceRegisteredListener {
        fun onDeviceRegistered(deviceId: String)
        fun onRegistrationSkipped()
        fun onRegistrationCancelled()
    }
    
    private var listener: OnDeviceRegisteredListener? = null
    private lateinit var deviceManager: DeviceIdentificationManager
    private var isFirstLaunch: Boolean = false
    private var allowSkip: Boolean = true
    
    companion object {
        fun newInstance(isFirstLaunch: Boolean = false, allowSkip: Boolean = true): DeviceRegistrationDialog {
            val dialog = DeviceRegistrationDialog()
            dialog.isFirstLaunch = isFirstLaunch
            dialog.allowSkip = allowSkip
            return dialog
        }
    }
    
    override fun onCreateDialog(savedInstanceState: Bundle?): Dialog {
        deviceManager = DeviceIdentificationManager.getInstance(requireContext())
        
        val view = LayoutInflater.from(context).inflate(R.layout.dialog_device_registration, null)
        val editTextDeviceId = view.findViewById<EditText>(R.id.editTextDeviceId)
        val textViewInfo = view.findViewById<TextView>(R.id.textViewInfo)
        
        // Pre-populate with current ID or suggested ID
        val currentId = deviceManager.getDeviceId()
        editTextDeviceId.setText(currentId ?: generateSuggestedDeviceId())
        
        val infoText = if (isFirstLaunch) {
            """
            Welcome to PsySuite!
            
            Would you like to register this device with a unique identifier?
            This helps track which device generated test data.
            
            You can skip this step and register later from the menu.
            
            Suggested format: Location-DeviceType-Number
            Examples: Lab1-Tablet-01, Office-Phone-A, Clinic-iPad-02
            """.trimIndent()
        } else {
            """
            Device Registration
            
            Provide a unique identifier for this PsySuite installation.
            This ID will be used to track which device generated test data.
            
            Current status: ${deviceManager.getRegistrationStatus()}
            
            Suggested format: Location-DeviceType-Number
            Examples: Lab1-Tablet-01, Office-Phone-A, Clinic-iPad-02
            """.trimIndent()
        }
        
        textViewInfo.text = infoText
        
        val builder = AlertDialog.Builder(requireContext())
            .setTitle(if (isFirstLaunch) "Welcome to PsySuite" else "Device Registration")
            .setView(view)
            .setPositiveButton("Register") { _, _ ->
                val deviceId = editTextDeviceId.text.toString().trim()
                if (validateDeviceId(deviceId)) {
                    deviceManager.setDeviceId(deviceId)
                    listener?.onDeviceRegistered(deviceId)
                } else {
                    showValidationError()
                }
            }
        
        if (allowSkip) {
            builder.setNeutralButton("Skip") { _, _ ->
                if (isFirstLaunch) {
                    deviceManager.skipRegistration()
                }
                listener?.onRegistrationSkipped()
            }
        }
        
        builder.setNegativeButton("Cancel") { _, _ ->
            listener?.onRegistrationCancelled()
        }
        
        builder.setCancelable(!isFirstLaunch) // Don't allow cancel on first launch
        
        return builder.create()
    }
    
    private fun generateSuggestedDeviceId(): String {
        val deviceInfo = Build.MODEL.replace(" ", "")
        val timestamp = SimpleDateFormat("MMdd", Locale.US).format(Date())
        return "PsySuite-$deviceInfo-$timestamp"
    }
    
    private fun validateDeviceId(deviceId: String): Boolean {
        return deviceId.length >= 3 && 
               deviceId.length <= 50 && 
               deviceId.matches(Regex("[a-zA-Z0-9\\-_]+"))
    }
    
    private fun showValidationError() {
        Toast.makeText(context, 
            "Device ID must be 3-50 characters, letters, numbers, hyphens and underscores only", 
            Toast.LENGTH_LONG).show()
    }
    
    fun setOnDeviceRegisteredListener(listener: OnDeviceRegisteredListener) {
        this.listener = listener
    }
}
```

#### 1.3 Application Startup Integration

```kotlin
class MainActivity : AppCompatActivity() {
    
    private lateinit var deviceManager: DeviceIdentificationManager
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        deviceManager = DeviceIdentificationManager.getInstance(this)
        
        // Check device registration on startup
        checkDeviceRegistration()
    }
    
    private fun checkDeviceRegistration() {
        if (deviceManager.isFirstLaunch()) {
            // Try to restore from backup first
            val backupManager = DeviceIdBackupManager(this)
            val restoredId = backupManager.restoreDeviceId()
            
            if (restoredId != null) {
                deviceManager.setDeviceId(restoredId)
                proceedWithNormalStartup()
            } else {
                showFirstLaunchRegistrationDialog()
            }
        } else {
            proceedWithNormalStartup()
        }
    }
    
    private fun showFirstLaunchRegistrationDialog() {
        val dialog = DeviceRegistrationDialog.newInstance(isFirstLaunch = true, allowSkip = true)
        dialog.setOnDeviceRegisteredListener(object : DeviceRegistrationDialog.OnDeviceRegisteredListener {
            override fun onDeviceRegistered(deviceId: String) {
                // Backup the device ID
                DeviceIdBackupManager(this@MainActivity).backupDeviceId(deviceId)
                
                // Show success message
                Toast.makeText(this@MainActivity, "Device registered as: $deviceId", Toast.LENGTH_LONG).show()
                
                proceedWithNormalStartup()
            }
            
            override fun onRegistrationSkipped() {
                // User chose to skip registration
                Toast.makeText(this@MainActivity, "Device registration skipped. You can register later from the menu.", Toast.LENGTH_LONG).show()
                
                proceedWithNormalStartup()
            }
            
            override fun onRegistrationCancelled() {
                // On first launch, treat cancel as skip
                deviceManager.skipRegistration()
                proceedWithNormalStartup()
            }
        })
        
        dialog.show(supportFragmentManager, "device_registration")
    }
    
    // Method to show registration dialog from menu
    fun showDeviceRegistrationFromMenu() {
        val dialog = DeviceRegistrationDialog.newInstance(isFirstLaunch = false, allowSkip = false)
        dialog.setOnDeviceRegisteredListener(object : DeviceRegistrationDialog.OnDeviceRegisteredListener {
            override fun onDeviceRegistered(deviceId: String) {
                // Backup the device ID
                DeviceIdBackupManager(this@MainActivity).backupDeviceId(deviceId)
                
                // Show success message
                Toast.makeText(this@MainActivity, "Device registered as: $deviceId", Toast.LENGTH_LONG).show()
            }
            
            override fun onRegistrationSkipped() {
                // Not applicable when called from menu
            }
            
            override fun onRegistrationCancelled() {
                // User cancelled, do nothing
            }
        })
        
        dialog.show(supportFragmentManager, "device_registration_menu")
    }
    
    private fun proceedWithNormalStartup() {
        // Continue with normal app initialization
        initializeApp()
    }
}
```

#### 1.4 Main Activity Menu Integration

```kotlin
// Add to MainActivity
override fun onCreateOptionsMenu(menu: Menu): Boolean {
    menuInflater.inflate(R.menu.main_menu, menu)
    return true
}

override fun onOptionsItemSelected(item: MenuItem): Boolean {
    return when (item.itemId) {
        R.id.action_device_registration -> {
            showDeviceRegistrationFromMenu()
            true
        }
        R.id.action_settings -> {
            startActivity(Intent(this, SettingsActivity::class.java))
            true
        }
        else -> super.onOptionsItemSelected(item)
    }
}
```

#### 1.5 Settings Integration

```kotlin
// Update SettingsFragment.kt
class SettingsFragment : PreferenceFragmentCompat(), Preference.OnPreferenceChangeListener {

    private lateinit var deviceManager: DeviceIdentificationManager
    private var deviceStatusPreference: Preference? = null
    private var deviceIdPreference: EditTextPreference? = null

    override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
        setPreferencesFromResource(R.xml.preferences, rootKey)
        
        deviceManager = DeviceIdentificationManager.getInstance(requireContext())
        
        setupDevicePreferences()
    }
    
    private fun setupDevicePreferences() {
        // Device status preference (read-only)
        deviceStatusPreference = findPreference<Preference>("device_status")
        deviceStatusPreference?.apply {
            title = "Device Registration Status"
            summary = deviceManager.getRegistrationStatus()
            isSelectable = false
        }
        
        // Device ID preference (editable)
        deviceIdPreference = findPreference<EditTextPreference>("device_id")
        deviceIdPreference?.apply {
            title = "Device Identifier"
            text = deviceManager.getDeviceId() ?: ""
            summary = if (deviceManager.isDeviceRegistered()) {
                "Current ID: ${deviceManager.getDeviceId()}"
            } else {
                "Not registered - tap to set device ID"
            }
            
            setOnPreferenceChangeListener { _, newValue ->
                val newId = newValue.toString().trim()
                if (validateDeviceId(newId)) {
                    deviceManager.setDeviceId(newId)
                    DeviceIdBackupManager(requireContext()).backupDeviceId(newId)
                    updateDevicePreferences()
                    true
                } else {
                    showValidationError()
                    false
                }
            }
        }
        
        // Register device preference (button)
        val registerDevicePreference = findPreference<Preference>("register_device")
        registerDevicePreference?.apply {
            title = "Register Device"
            summary = "Open device registration dialog"
            setOnPreferenceClickListener {
                showDeviceRegistrationDialog()
                true
            }
        }
        
        // Clear registration preference (button)
        val clearRegistrationPreference = findPreference<Preference>("clear_device_registration")
        clearRegistrationPreference?.apply {
            title = "Clear Device Registration"
            summary = "Remove device identifier"
            isVisible = deviceManager.isDeviceRegistered()
            setOnPreferenceClickListener {
                showClearRegistrationDialog()
                true
            }
        }
    }
    
    private fun updateDevicePreferences() {
        deviceStatusPreference?.summary = deviceManager.getRegistrationStatus()
        deviceIdPreference?.apply {
            text = deviceManager.getDeviceId() ?: ""
            summary = if (deviceManager.isDeviceRegistered()) {
                "Current ID: ${deviceManager.getDeviceId()}"
            } else {
                "Not registered - tap to set device ID"
            }
        }
        
        findPreference<Preference>("clear_device_registration")?.isVisible = deviceManager.isDeviceRegistered()
    }
    
    private fun showDeviceRegistrationDialog() {
        val dialog = DeviceRegistrationDialog.newInstance(isFirstLaunch = false, allowSkip = false)
        dialog.setOnDeviceRegisteredListener(object : DeviceRegistrationDialog.OnDeviceRegisteredListener {
            override fun onDeviceRegistered(deviceId: String) {
                DeviceIdBackupManager(requireContext()).backupDeviceId(deviceId)
                updateDevicePreferences()
                Toast.makeText(context, "Device registered as: $deviceId", Toast.LENGTH_LONG).show()
            }
            
            override fun onRegistrationSkipped() {
                // Not applicable in settings
            }
            
            override fun onRegistrationCancelled() {
                // User cancelled, do nothing
            }
        })
        
        dialog.show(parentFragmentManager, "device_registration_settings")
    }
    
    private fun showClearRegistrationDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle("Clear Device Registration")
            .setMessage("Are you sure you want to clear the device registration? This will remove the device identifier from future experiment uploads.")
            .setPositiveButton("Clear") { _, _ ->
                deviceManager.clearRegistration()
                updateDevicePreferences()
                Toast.makeText(context, "Device registration cleared", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun validateDeviceId(deviceId: String): Boolean {
        return deviceId.length >= 3 && 
               deviceId.length <= 50 && 
               deviceId.matches(Regex("[a-zA-Z0-9\\-_]+"))
    }
    
    private fun showValidationError() {
        Toast.makeText(context, 
            "Device ID must be 3-50 characters, letters, numbers, hyphens and underscores only", 
            Toast.LENGTH_LONG).show()
    }

    override fun onPreferenceChange(preference: Preference, value: Any?): Boolean {
        return true
    }
}
```

#### 1.5 Data Upload Integration

```kotlin
// Update SubjectBasicParcel to include device ID
@Parcelize
open class SubjectBasicParcel(
    // ... existing fields ...
    
    // New field for device identification
    open var deviceId: String = "",
    
    // ... rest of fields ...
) : Parcelable

// Update ResultsManager to include device registration check and device ID handling
class ResultsManager private constructor(private val activity: Activity) {
    
    private val deviceManager = DeviceIdentificationManager.getInstance(activity)
    
    fun onTestFinished(result: TestResult) {
        // Check whether test defined specific recipients. otherwise use the default one(s)
        val ci = getCompanionObjectMethod(result.testClass, "getEmailRecipients")
        if(ci.first != null) emailRecipients = ci.first?.call(ci.second) as Array<String>
        
        // Add device ID to the result if device is registered
        if (deviceManager.isDeviceRegistered()) {
            result.subjectParcel.deviceId = deviceManager.getDeviceId()!!
        }
        
        // Check device registration status and decide upload strategy
        if (deviceManager.isDeviceRegistered()) {
            // Device is registered - proceed with web upload if enabled
            if (webUploadEnabled && result.res_files.isNotEmpty()) {
                if(result.code == TestBasic.TEST_COMPLETED) {
                    uploadToWebBackend(result)
                } else {
                    askWhetherUploadingToWeb(result)
                }
            }
            // Fallback to email if web upload is disabled but device is registered
            else if(sendResult && result.res_files.isNotEmpty()){
                if(result.code == TestBasic.TEST_COMPLETED) sendResult(result)
                else askWhetherSending(result)
            }
            else {
                showTestCompletionMessage(result.code)
            }
        } else {
            // Device is not registered - ask user what to do
            askUnregisteredDeviceAction(result)
        }
    }
    
    private fun askUnregisteredDeviceAction(result: TestResult) {
        show2ChoisesDialog(
            activity, 
            resources.getString(R.string.warning), 
            "Device not registered. Would you like to send results via email instead?", 
            resources.getString(R.string.yes), 
            resources.getString(R.string.no),
            { 
                // User chose to send via email
                if(result.res_files.isNotEmpty()) {
                    if(result.code == TestBasic.TEST_COMPLETED) sendResult(result)
                    else askWhetherSending(result)
                } else {
                    showTestCompletionMessage(result.code)
                }
            },
            { 
                // User chose not to send - just show completion message
                showTestCompletionMessage(result.code)
            }
        )
    }
    
    private fun showTestCompletionMessage(code: Int) {
        when(code){
            TestBasic.TEST_COMPLETED -> showAlert(activity, resources.getString(R.string.onend_test), resources.getString(R.string.test_completed_success))
            TestBasic.TEST_ABORTED_DEL_RESULT,
            TestBasic.TEST_ABORTED_KEEP_RESULT,
            TestBasic.TEST_ABORTED_WITH_ERROR -> showAlert(activity, resources.getString(R.string.onend_test), resources.getString(R.string.test_completed_abort))
            TestBasic.BLOCK_COMPLETED -> showAlert(activity, resources.getString(R.string.onend_test), resources.getString(R.string.test_partially_completed))
        }
    }
    
    private fun uploadToWebBackend(result: TestResult) {
        uploadJob = GlobalScope.launch {
            try {
                withContext(Dispatchers.Main) {
                    mailAD = show1MethodDialog(activity, "Upload", "Uploading results to web backend...", resources.getString(R.string.abort)){
                        uploadJob.cancel()
                        mailAD?.dismiss()
                        mailAD = null
                    }
                }

                val experimentData = parseExperimentFiles(result)
                if (experimentData != null) {
                    // Ensure device ID is included in experiment data
                    if (deviceManager.isDeviceRegistered()) {
                        experimentData.deviceId = deviceManager.getDeviceId()!!
                    }
                    
                    val success = doUploadExperiment(experimentData)

                    withContext(Dispatchers.Main) {
                        mailAD?.dismiss()

                        if (success) {
                            moveFilesToPrivateStorage(result.res_files)
                            showAlert(activity, resources.getString(R.string.success), "Results uploaded successfully")
                        } else {
                            showAlert(activity, resources.getString(R.string.failure), "Upload failed. Results saved locally for retry.")
                        }
                    }
                } else {
                    withContext(Dispatchers.Main) {
                        mailAD?.dismiss()
                        showAlert(activity, resources.getString(R.string.failure), "Failed to parse experiment data")
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    mailAD?.dismiss()
                    showAlert(activity, resources.getString(R.string.failure), "Upload error: ${e.message}")
                }
                android.util.Log.e("ResultsManager", "Upload error", e)
            }
        }
    }
}
```

### 2. Web Backend Implementation

#### 2.1 Database Schema Updates

```sql
-- Add device_id column to experiments table
ALTER TABLE experiments ADD COLUMN device_id VARCHAR(50);
CREATE INDEX idx_experiments_device_id ON experiments(device_id);

-- Create device registry table
CREATE TABLE device_registry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_experiments INTEGER DEFAULT 0,
    device_info JSONB,
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 2.2 Experiment Model Updates

```python
# Update Experiment model
class Experiment(db.Model):
    # ... existing fields ...
    
    # New device identification field
    device_id = db.Column(db.String(50), index=True)
    
    # ... rest of model ...
    
    def to_dict(self, include_trials=False):
        result = {
            # ... existing fields ...
            'device_id': self.device_id,
            # ... rest of fields ...
        }
        return result
```

#### 2.3 Device Registry Model

```python
class DeviceRegistry(db.Model):
    __tablename__ = 'device_registry'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    total_experiments = db.Column(db.Integer, default=0)
    device_info = db.Column(db.JSON)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<DeviceRegistry {self.device_id}>'
    
    @staticmethod
    def register_or_update_device(device_id, device_info=None):
        device = DeviceRegistry.query.filter_by(device_id=device_id).first()
        
        if device:
            # Update existing device
            device.last_seen = datetime.utcnow()
            device.total_experiments += 1
            if device_info:
                device.device_info = device_info
        else:
            # Register new device
            device = DeviceRegistry(
                device_id=device_id,
                device_info=device_info,
                total_experiments=1
            )
            db.session.add(device)
        
        db.session.commit()
        return device
```

#### 2.4 Upload API Updates

```python
@bp.route('/upload/experiment', methods=['POST'])
def upload_experiment():
    try:
        data = request.get_json()
        
        # Validate device ID
        device_id = data.get('device_id') or data.get('configuration', {}).get('deviceId')
        if not device_id:
            return jsonify({
                'success': False,
                'message': 'Device ID is required'
            }), 400
        
        # Register or update device
        DeviceRegistry.register_or_update_device(
            device_id=device_id,
            device_info=data.get('configuration', {}).get('device')
        )
        
        # Create experiment with device ID
        experiment = Experiment(
            exp_uid=data['exp_uid'],
            test_id=test.id,
            device_id=device_id,
            # ... other fields ...
        )
        
        # ... rest of upload logic ...
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Upload failed',
            'error': str(e)
        }), 500
```

#### 2.5 Web Interface Updates

```python
# Add device filtering to experiments view
@bp.route('/experiments')
@login_required
def experiments():
    device_id = request.args.get('device_id')
    
    query = Experiment.query
    if device_id:
        query = query.filter_by(device_id=device_id)
    
    experiments = query.order_by(db.desc(Experiment.uploaded_at)).all()
    devices = DeviceRegistry.query.filter_by(is_active=True).all()
    
    return render_template('experiments.html', 
                         experiments=experiments, 
                         devices=devices,
                         selected_device=device_id)

# Device management page
@bp.route('/admin/devices')
@admin_required
def manage_devices():
    devices = DeviceRegistry.query.order_by(db.desc(DeviceRegistry.last_seen)).all()
    return render_template('admin/devices.html', devices=devices)
```

## Persistence Strategy

### Why This Approach Works Across Updates:

1. **SharedPreferences**: Survives app updates (not uninstalls)
2. **Internal File Backup**: Additional persistence layer
3. **Server Registry**: Web backend tracks all known devices
4. **Multiple Recovery Points**: If one fails, others provide backup

### Update Scenarios:

| Scenario | SharedPreferences | File Backup | Server Registry | Result |
|----------|------------------|-------------|-----------------|---------|
| App Update | ✅ Preserved | ✅ Preserved | ✅ Available | ID Maintained |
| App Reinstall | ❌ Lost | ❌ Lost | ✅ Available | Manual Re-entry |
| Device Reset | ❌ Lost | ❌ Lost | ✅ Available | Manual Re-entry |
| New Device | ❌ N/A | ❌ N/A | ❌ N/A | New Registration |

## Security Considerations

1. **No Sensitive Data**: Device ID contains no personal information
2. **User Control**: Users can change device ID anytime
3. **Validation**: Server validates device ID format and uniqueness
4. **Audit Trail**: All device registrations are logged

### 3. XML Resources

#### 3.1 Menu Resource (res/menu/main_menu.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto">
    
    <item
        android:id="@+id/action_device_registration"
        android:title="Register Device"
        android:icon="@drawable/ic_device"
        app:showAsAction="never" />
    
    <item
        android:id="@+id/action_settings"
        android:title="Settings"
        android:icon="@drawable/ic_settings"
        app:showAsAction="never" />
        
</menu>
```

#### 3.2 Updated Preferences XML (res/xml/preferences.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<PreferenceScreen xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- Device Registration Category -->
    <PreferenceCategory
        android:title="Device Registration"
        android:key="device_category">
        
        <Preference
            android:key="device_status"
            android:title="Registration Status"
            android:summary="Not registered"
            android:selectable="false" />
            
        <EditTextPreference
            android:key="device_id"
            android:title="Device Identifier"
            android:summary="Tap to set device ID"
            android:dialogTitle="Device Identifier"
            android:dialogMessage="Enter a unique identifier for this device (3-50 characters, letters, numbers, hyphens, underscores only)" />
            
        <Preference
            android:key="register_device"
            android:title="Register Device"
            android:summary="Open device registration dialog" />
            
        <Preference
            android:key="clear_device_registration"
            android:title="Clear Registration"
            android:summary="Remove device identifier"
            android:visible="false" />
            
    </PreferenceCategory>
    
    <!-- Existing preferences continue here -->
    
</PreferenceScreen>
```

#### 3.3 Registration Dialog Layout (res/layout/dialog_device_registration.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:padding="16dp">

    <TextView
        android:id="@+id/textViewInfo"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginBottom="16dp"
        android:text="Device registration information"
        android:textSize="14sp" />

    <com.google.android.material.textfield.TextInputLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Device Identifier">

        <com.google.android.material.textfield.TextInputEditText
            android:id="@+id/editTextDeviceId"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:inputType="text"
            android:maxLength="50" />

    </com.google.android.material.textfield.TextInputLayout>

    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout_marginTop="8dp"
        android:text="Examples: Lab1-Tablet-01, Office-Phone-A, Clinic-iPad-02"
        android:textSize="12sp"
        android:textStyle="italic" />

</LinearLayout>
```

## Updated User Experience Flow

### First Launch Experience:
1. **Welcome Dialog**: "Welcome to PsySuite! Would you like to register this device?"
2. **Options**: [Register] [Skip] [Cancel]
3. **If Skip**: "Registration skipped. You can register later from the menu."
4. **If Register**: Normal registration flow

### Menu Access:
1. **Three-dots menu** → "Register Device"
2. **Settings** → "Device Registration" section
3. **Multiple options**: View status, register, edit ID, clear registration

### Settings Integration:
- **Registration Status**: Shows current state
- **Device Identifier**: Direct edit field
- **Register Device**: Opens full dialog
- **Clear Registration**: Removes device ID

## Implementation Priority

1. **Phase 1**: Optional device ID storage and first-launch dialog
2. **Phase 2**: Menu integration and settings preferences
3. **Phase 3**: Web backend integration and device registry
4. **Phase 4**: Advanced device management and analytics

## Key Benefits

✅ **User Choice**: Registration is optional, not forced
✅ **Easy Access**: Three-dots menu provides quick access
✅ **Flexible Management**: Multiple ways to manage device ID
✅ **Persistent**: Survives app updates
✅ **Recoverable**: Multiple backup mechanisms
✅ **User-Friendly**: Clear status and easy modification

This design ensures robust device identification that persists across app updates while providing maximum flexibility for users and administrators to manage device identities effectively.
## Res
ultsManager Integration Updates

### Updated Data Classes

```kotlin
// Updated data classes for upload with device ID support
data class ExperimentUploadData(
    val exp_uid: String,
    val testClassName: String,
    val configuration: JSONObject,
    val trials: List<TrialData>,
    var deviceId: String = "" // Device identifier for tracking
)

data class TrialData(
    val trialNumber: Int,
    val data: Map<String, Any>
)
```

### Updated Upload Payload Structure

```kotlin
// Updated JSON payload creation in doUploadExperiment
val payload = JSONObject().apply {
    put("exp_uid", experimentData.exp_uid)
    put("test_class_name", experimentData.testClassName)
    put("device_id", experimentData.deviceId) // Include device ID
    put("configuration", experimentData.configuration)
    put("trials", JSONArray().apply {
        experimentData.trials.forEach { trial ->
            put(JSONObject().apply {
                put("trid", trial.trialNumber)
                trial.data.forEach { (key, value) ->
                    put(key, value)
                }
            })
        }
    })
}
```

### SubjectBasicParcel Updates

```kotlin
// Add deviceId field to SubjectBasicParcel
@Parcelize
open class SubjectBasicParcel(
    // ... existing fields ...
    
    // New field for device identification
    open var deviceId: String = "",
    
    // ... rest of fields ...
) : Parcelable
```

### Key Integration Points

1. **Device Registration Check**: `onTestFinished()` now checks if device is registered before deciding upload strategy
2. **Device ID Population**: Device ID is added to `result.subjectParcel.deviceId` when device is registered
3. **Unregistered Device Handling**: If device is not registered, user is asked whether to send via email or skip
4. **Upload Payload**: Device ID is included in the JSON payload sent to web backend
5. **Fallback Strategy**: Email sending is offered as fallback for unregistered devices

### Flow Decision Logic

```
onTestFinished(result) {
    if (deviceManager.isDeviceRegistered()) {
        result.subjectParcel.deviceId = deviceManager.getDeviceId()
        
        if (webUploadEnabled) {
            uploadToWebBackend(result)
        } else if (sendResult) {
            sendResult(result) // email fallback
        } else {
            showCompletionMessage()
        }
    } else {
        askUnregisteredDeviceAction(result) {
            // Options: Send via email OR Do nothing
        }
    }
}
```

This integration ensures that:
- Only registered devices can upload to web backend
- Unregistered devices are offered email as alternative
- Device ID is consistently tracked across all data uploads
- User has clear options when device is not registered