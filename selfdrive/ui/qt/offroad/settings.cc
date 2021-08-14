#include "selfdrive/ui/qt/offroad/settings.h"

#include <cassert>
#include <string>

#include <QDebug>

#ifndef QCOM
#include "selfdrive/ui/qt/offroad/networking.h"
#endif

#ifdef ENABLE_MAPS
#include "selfdrive/ui/qt/maps/map_settings.h"
#endif

#include "selfdrive/common/params.h"
#include "selfdrive/common/util.h"
#include "selfdrive/hardware/hw.h"
#include "selfdrive/ui/qt/widgets/controls.h"
#include "selfdrive/ui/qt/widgets/input.h"
#include "selfdrive/ui/qt/widgets/scrollview.h"
#include "selfdrive/ui/qt/widgets/ssh_keys.h"
#include "selfdrive/ui/qt/widgets/toggle.h"
#include "selfdrive/ui/ui.h"
#include "selfdrive/ui/qt/util.h"
#include "selfdrive/ui/qt/qt_window.h"

TogglesPanel::TogglesPanel(QWidget *parent) : QWidget(parent) {
  QVBoxLayout *main_layout = new QVBoxLayout(this);
  main_layout->setSpacing(20);
  QList<ParamControl*> toggles;

  toggles.append(new ParamControl("OpenpilotEnabledToggle",
                                  //"Enable openpilot",
                                  //"Use the openpilot system for adaptive cruise control and lane keep driver assistance. Your attention is required at all times to use this feature. Changing this setting takes effect when the car is powered off.",
                                  "Enable openpilot",
                                  "Use the openpilot system for adaptive cruise control and lane keep driver assistance. Your attention is required at all times to use this feature. Changing this setting takes effect when the car is powered off.",
                                  "../assets/offroad/icon_openpilot.png",
                                  this));
/*
  toggles.append(new ParamControl("IsRHD",
                                  "Enable Right-Hand Drive",
                                  "Allow openpilot to obey left-hand traffic conventions and perform driver monitoring on right driver seat.",
                                  "../assets/offroad/icon_openpilot_mirrored.png",
                                  this));
*/
  toggles.append(new ParamControl("IsMetric",
                                  //"Use Metric System",
                                  //"Display speed in km/h instead of mp/h.",
                                  "Use Metric System",
                                  "Display speed in km/h instead of mp/h.",
                                  "../assets/offroad/icon_metric.png",
                                  this));
  toggles.append(new ParamControl("CommunityFeaturesToggle",
                                  //"Enable Community Features",
                                  //"Use features from the open source community that are not maintained or supported by comma.ai and have not been confirmed to meet the standard safety model. These features include community supported cars and community supported hardware. Be extra cautious when using these features",
                                  "Enable Community Features",
                                  "Use features from the open source community that are not maintained or supported by comma.ai and have not been confirmed to meet the standard safety model. These features include community supported cars and community supported hardware. Be extra cautious when using these features",
                                  "../assets/offroad/icon_discord.png",
                                  this));
  toggles.append(new ParamControl("IsLdwEnabled",
                                  //"Enable Lane Departure Warnings",
                                  //"Receive alerts to steer back into the lane when your vehicle drifts over a detected lane line without a turn signal activated while driving over 31mph (50kph).",
                                  "Enable Lane Departure Warnings",
                                  "Receive alerts to steer back into the lane when your vehicle drifts over a detected lane line without a turn signal activated while driving over 31mph (50kph).",
                                  "../assets/offroad/icon_ldws.png",
                                  this));
  toggles.append(new ParamControl("AutoLaneChangeEnabled",
                                  //"Enable AutoLaneChange",
                                  //"Operation of the turn signal at 60㎞/h speed will result in a short change of the vehicle",
                                  "Enable AutoLaneChange",
                                  "Operation of the turn signal at 60㎞/h speed will result in a short change of the vehicle",
                                  "../assets/offroad/icon_lca.png",
                                  this));
  toggles.append(new ParamControl("UploadRaw",
                                  //"Upload Raw Logs",
                                  //"Upload full logs at [ connect.comma.ai/useradmin ]",
                                  "Upload Raw Logs",
                                  "Upload full logs at [ connect.comma.ai/useradmin ]",
                                  "../assets/offroad/icon_network.png",
                                  this));
  toggles.append(new ParamControl("EndToEndToggle",
                                  "\U0001f96c Disable use of lanelines (Alpha) \U0001f96c",
                                  "In this mode openpilot will ignore lanelines and just drive how it thinks a human would.",
                                  "../assets/offroad/icon_road.png",
                                  this));
/*
  ParamControl *record_toggle = new ParamControl("RecordFront",
                                                 "Record and Upload Driver Camera",
                                                 "Upload data from the driver facing camera and help improve the driver monitoring algorithm.",
                                                 "../assets/offroad/icon_monitoring.png",
                                                 this);
  toggles.append(record_toggle);

#ifdef ENABLE_MAPS
  toggles.append(new ParamControl("NavSettingTime24h",
                                  "Show ETA in 24h format",
                                  "Use 24h format instead of am/pm",
                                  "../assets/offroad/icon_metric.png",
                                  this));
#endif

  bool record_lock = Params().getBool("RecordFrontLock");
  record_toggle->setEnabled(!record_lock);
*/
  for(ParamControl *toggle : toggles) {
    if(main_layout->count() != 0) {
    }
    main_layout->addWidget(toggle);
  }
  main_layout->addWidget(horizontal_line());
  main_layout->addWidget(new LabelControl(" ▼  Toggle Community Add-ons", ""));
  main_layout->addWidget(new ParamControl("PutPrebuilt", "Prebuilt Enable",
                                  //"Create prebuilt files to speed bootup",
                                  "Create prebuilt files to speed bootup",
                                  "../assets/offroad/icon_addon.png", this));
  main_layout->addWidget(new ParamControl("DisableShutdownd", "Shutdown Disable",
                                  //"Disable Shutdownd",
                                  "Disable Shutdown",
                                  "../assets/offroad/icon_addon.png", this));
  main_layout->addWidget(new ParamControl("DisableLogger", "Logger Disable",
                                  //"Disable Logger is Reduce system load",
                                  "Disable Logger is Reduce system load",
                                  "../assets/offroad/icon_addon.png", this));
  main_layout->addWidget(new ParamControl("DisableGps", "GPS Disable",
                                  //"If you're using a panda without GPS, activate the option",
                                  "If you're using a panda without GPS, activate the option",
                                  "../assets/offroad/icon_addon.png", this));
  main_layout->addWidget(new ParamControl("UiTpms", "Ui Tpms Enable",
                                  //"Ui Tpms Enable (HKG only)",
                                  "Ui Tpms Enable (HKG only)",
                                  "../assets/offroad/icon_addon.png", this));
}

DevicePanel::DevicePanel(QWidget* parent) : QWidget(parent) {
  QVBoxLayout *main_layout = new QVBoxLayout(this);
  main_layout->setSpacing(20);
  Params params = Params();

  QString dongle = QString::fromStdString(params.get("DongleId", false));
  //main_layout->addWidget(new LabelControl("Dongle ID", dongle));
  main_layout->addWidget(new LabelControl("Dongle ID", dongle));
/*
  main_layout->addWidget(horizontal_line());

  QString serial = QString::fromStdString(params.get("HardwareSerial", false));
  main_layout->addWidget(new LabelControl("Serial", serial));
*/
  // offroad-only buttons

  //auto dcamBtn = new ButtonControl("Driver Camera", "PREVIEW", "Preview the driver facing camera to help optimize device mounting position for best driver monitoring experience. (vehicle must be off)");
  auto dcamBtn = new ButtonControl("Driver Camera", "PREVIEW", "Preview the driver facing camera to help optimize device mounting position for best driver monitoring experience. (vehicle must be off)");
  connect(dcamBtn, &ButtonControl::clicked, [=]() { emit showDriverView(); });

  QString resetCalibDesc = "Range within (pitch) ↕ 5˚ (yaw) ↔ 4˚";
  //auto resetCalibBtn = new ButtonControl("Reset Calibration", "RESET", resetCalibDesc);Driver Camera", "PREVIEW", "Preview the driver facing camera to help optimize device mounting position for best driver monitoring experience. (vehicle must be off)")
  auto resetCalibBtn = new ButtonControl("Reset Calibration", "RESET", resetCalibDesc);
  connect(resetCalibBtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Are you sure you want to reset calibration?", this)) {
    if (ConfirmationDialog::confirm("Are you sure you want to reset calibration?", this)) {
      Params().remove("CalibrationParams");
      Params().remove("LiveParameters");
      QTimer::singleShot(1000, []() { Hardware::reboot(); });
    }
  });
  connect(resetCalibBtn, &ButtonControl::showDescription, [=]() {
    QString desc = resetCalibDesc;
    std::string calib_bytes = Params().get("CalibrationParams");
    if (!calib_bytes.empty()) {
      try {
        AlignedBuffer aligned_buf;
        capnp::FlatArrayMessageReader cmsg(aligned_buf.align(calib_bytes.data(), calib_bytes.size()));
        auto calib = cmsg.getRoot<cereal::Event>().getLiveCalibration();
        if (calib.getCalStatus() != 0) {
          double pitch = calib.getRpyCalib()[1] * (180 / M_PI);
          double yaw = calib.getRpyCalib()[2] * (180 / M_PI);
          //desc += QString("\nThe current calibration location is [ %2 %1° / %4 %3° ]")
          desc += QString("\nThe current calibration location is [ %2 %1° / %4 %3° ]")
                                .arg(QString::number(std::abs(pitch), 'g', 1), pitch > 0 ? "↑" : "↓",
                                     QString::number(std::abs(yaw), 'g', 1), yaw > 0 ? "→" : "←");
        }
      } catch (kj::Exception) {
        //qInfo() << "invalid CalibrationParams";
        qInfo() << "Calibration status is invalid";
      }
    }
    resetCalibBtn->setDescription(desc);
  });

  ButtonControl *retrainingBtn = nullptr;
  if (!params.getBool("Passive")) {
    //retrainingBtn = new ButtonControl("Review Training Guide", "REVIEW", "Review the rules, features, and limitations of openpilot");
    retrainingBtn = new ButtonControl("Review Training Guide", "REVIEW", "");
    connect(retrainingBtn, &ButtonControl::clicked, [=]() {
      //if (ConfirmationDialog::confirm("Are you sure you want to review the training guide?", this)) {
      if (ConfirmationDialog::confirm("Are you sure you want to review the training guide?", this)) {
        Params().remove("CompletedTrainingVersion");
        emit reviewTrainingGuide();
      }
    });
  }

  //auto uninstallBtn = new ButtonControl("Uninstall " + getBrand(), "UNINSTALL");
  auto uninstallBtn = new ButtonControl(getBrand() + " Uninstall", "UNINSTALL");
  connect(uninstallBtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Are you sure you want to uninstall?", this)) {
    if (ConfirmationDialog::confirm("Are you sure you want to uninstall?", this)) {
      Params().putBool("DoUninstall", true);
    }
  });

  ButtonControl *regulatoryBtn = nullptr;
  if (Hardware::TICI()) {
    regulatoryBtn = new ButtonControl("Regulatory", "VIEW", "");
    connect(regulatoryBtn, &ButtonControl::clicked, [=]() {
      const std::string txt = util::read_file(ASSET_PATH.toStdString() + "/offroad/fcc.html");
      RichTextDialog::alert(QString::fromStdString(txt), this);
    });
  }

  for (auto btn : {dcamBtn, resetCalibBtn, retrainingBtn, uninstallBtn, regulatoryBtn}) {
    if (btn) {
      connect(parent, SIGNAL(offroadTransition(bool)), btn, SLOT(setEnabled(false)));
      main_layout->addWidget(btn);
    }
  }

  // power buttons
  QHBoxLayout *power_layout = new QHBoxLayout();
  power_layout->setSpacing(30);

  //QPushButton *reboot_btn = new QPushButton("Reboot");
  QPushButton *reboot_btn = new QPushButton("Reboot");
  reboot_btn->setObjectName("reboot_btn");
  power_layout->addWidget(reboot_btn);
  QObject::connect(reboot_btn, &QPushButton::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Are you sure you want to reboot?", this)) {
    if (ConfirmationDialog::confirm("Are you sure you want to reboot?", this)) {
      Hardware::reboot();
    }
  });

  //QPushButton *poweroff_btn = new QPushButton("Power Off");
  QPushButton *poweroff_btn = new QPushButton("Power Off");
  poweroff_btn->setObjectName("poweroff_btn");
  power_layout->addWidget(poweroff_btn);
  QObject::connect(poweroff_btn, &QPushButton::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Are you sure you want to power off?", this)) {
    if (ConfirmationDialog::confirm("Are you sure you want to power off?", this)) {
      Hardware::poweroff();
    }
  });

  setStyleSheet(R"(
    QPushButton {
      height: 120px;
      border-radius: 15px;
    }
    #reboot_btn { background-color: #2CE22C; }
    #reboot_btn:pressed { background-color: #4a4a4a; }
    #poweroff_btn { background-color: #E22C2C; }
    #poweroff_btn:pressed { background-color: #FF2424; }
  )");
  main_layout->addLayout(power_layout);
}

SoftwarePanel::SoftwarePanel(QWidget* parent) : QWidget(parent) {
  gitRemoteLbl = new LabelControl("Git Remote");
  gitBranchLbl = new LabelControl("Git Branch");
  gitCommitLbl = new LabelControl("Git Commit");
  osVersionLbl = new LabelControl("NEOS Version");
  versionLbl = new LabelControl("Version");
  lastUpdateLbl = new LabelControl("Last Update Check", "", "The last time openpilot successfully checked for an update. The updater only runs while the car is off.");
  updateBtn = new ButtonControl("Check for Update", "");
  connect(updateBtn, &ButtonControl::clicked, [=]() {
    if (params.getBool("IsOffroad")) {
      const QString paramsPath = QString::fromStdString(params.getParamsPath());
      fs_watch->addPath(paramsPath + "/d/LastUpdateTime");
      fs_watch->addPath(paramsPath + "/d/UpdateFailedCount");
      updateBtn->setText("CHECKING");
      updateBtn->setEnabled(false);
    }
    std::system("pkill -1 -f selfdrive.updated");
  });

  QVBoxLayout *main_layout = new QVBoxLayout(this);
  main_layout->setSpacing(20);
  QWidget *widgets[] = {versionLbl, gitRemoteLbl, gitBranchLbl, gitCommitLbl, osVersionLbl};
  for (int i = 0; i < std::size(widgets); ++i) {
    main_layout->addWidget(widgets[i]);
    if (i < std::size(widgets) - 1) {
    }
  }

  fs_watch = new QFileSystemWatcher(this);
  QObject::connect(fs_watch, &QFileSystemWatcher::fileChanged, [=](const QString path) {
    int update_failed_count = params.get<int>("UpdateFailedCount").value_or(0);
    if (path.contains("UpdateFailedCount") && update_failed_count > 0) {
      lastUpdateLbl->setText("failed to fetch update");
      updateBtn->setText("CHECK");
      updateBtn->setEnabled(true);
    } else if (path.contains("LastUpdateTime")) {
      updateLabels();
    }
  });
}

void SoftwarePanel::showEvent(QShowEvent *event) {
  updateLabels();
}

void SoftwarePanel::updateLabels() {
  QString lastUpdate = "";
  auto tm = params.get("LastUpdateTime");
  if (!tm.empty()) {
    lastUpdate = timeAgo(QDateTime::fromString(QString::fromStdString(tm + "Z"), Qt::ISODate));
  }

  versionLbl->setText(getBrandVersion());
  lastUpdateLbl->setText(lastUpdate);
  updateBtn->setText("CHECK");
  updateBtn->setEnabled(true);
  gitRemoteLbl->setText(QString::fromStdString(params.get("GitRemote").substr(19)));
  gitBranchLbl->setText(QString::fromStdString(params.get("GitBranch")));
  gitCommitLbl->setText(QString::fromStdString(params.get("GitCommit")).left(7));
  osVersionLbl->setText(QString::fromStdString(Hardware::get_os_version()).trimmed());
}

QWidget * network_panel(QWidget * parent) {
  QWidget *w = new QWidget(parent);
  QVBoxLayout *layout = new QVBoxLayout(w);
  layout->setSpacing(20);
#ifdef QCOM
  //auto wifiBtn = new ButtonControl("WiFi Settings", "OPEN");
  auto wifiBtn = new ButtonControl("\U0001f4f6 WiFi Settings", "OPEN");
  QObject::connect(wifiBtn, &ButtonControl::clicked, [=]() { HardwareEon::launch_wifi(); });
  layout->addWidget(wifiBtn);

  //auto tetheringBtn = new ButtonControl("Tethering Settings", "OPEN");
  auto tetheringBtn = new ButtonControl("\U0001f4f6 Tethering Settings", "OPEN");
  QObject::connect(tetheringBtn, &ButtonControl::clicked, [=]() { HardwareEon::launch_tethering(); });
  layout->addWidget(tetheringBtn);

  //auto androidBtn = new ButtonControl("\U00002699 Android Settings", "OPEN");
  auto androidBtn = new ButtonControl("\U00002699 Android Settings", "OPEN");
  QObject::connect(androidBtn, &ButtonControl::clicked, [=]() { HardwareEon::launch_setting(); });
  layout->addWidget(androidBtn);

  layout->addWidget(horizontal_line());
#endif

  // SSH key management
  layout->addWidget(new SshToggle());
  layout->addWidget(new SshControl());
  layout->addWidget(horizontal_line());
  layout->addWidget(new LateralControlSelect());
  layout->addWidget(new MfcSelect());
  layout->addWidget(new LongControlSelect());
  layout->addWidget(horizontal_line());

  const char* gitpull = "sh /data/openpilot/gitpull.sh";
  //auto gitpullbtn = new ButtonControl("Git Fetch and Reset", "RUN");
  auto gitpullbtn = new ButtonControl("Git Fetch and Reset", "RUN");
  QObject::connect(gitpullbtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Process?", w)){
    if (ConfirmationDialog::confirm("Process?", w)){
      std::system(gitpull);
      QTimer::singleShot(1000, []() { Hardware::reboot(); });
    }
  });
  layout->addWidget(gitpullbtn);

  const char* panda_flash = "sh /data/openpilot/panda/board/flash.sh";
  //auto pandaflashbtn = new ButtonControl("Panda Firmware Flash", "RUN");
  auto pandaflashbtn = new ButtonControl("Panda Firmware Flash", "RUN");
  QObject::connect(pandaflashbtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Process?", w)){
    if (ConfirmationDialog::confirm("Process?", w)){
      std::system(panda_flash);
      QTimer::singleShot(1000, []() { Hardware::reboot(); });
    }
  });
  layout->addWidget(pandaflashbtn);

  const char* panda_recover = "sh /data/openpilot/panda/board/recover.sh";
  //auto pandarecoverbtn = new ButtonControl("Panda Firmware Recover", "RUN");
  auto pandarecoverbtn = new ButtonControl("Panda Firmware Recover", "RUN");
  QObject::connect(pandarecoverbtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Process?", w)){
    if (ConfirmationDialog::confirm("Process?", w)){
      std::system(panda_recover);
      QTimer::singleShot(1000, []() { Hardware::reboot(); });
    }
  });
  layout->addWidget(pandarecoverbtn);

  const char* addfunc = "cp -f /data/openpilot/installer/fonts/driver_monitor.py /data/openpilot/selfdrive/monitoring";
  //auto addfuncbtn = new ButtonControl("Add Function", "RUN");
  auto addfuncbtn = new ButtonControl("Add Function", "RUN");
  QObject::connect(addfuncbtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Process?", w)){
    if (ConfirmationDialog::confirm("Process?", w)) {
      std::system(addfunc);
      QTimer::singleShot(1000, []() { Hardware::reboot(); });
    }
  });
  layout->addWidget(addfuncbtn);

  const char* realdata_clear = "rm -rf /sdcard/realdata/*";
  //auto realdataclearbtn = new ButtonControl("Driving log Delete", "RUN");
  auto realdataclearbtn = new ButtonControl("Driving log Delete", "RUN");
  QObject::connect(realdataclearbtn, &ButtonControl::clicked, [=]() {
    //if (ConfirmationDialog::confirm("Process?", w)){
    if (ConfirmationDialog::confirm("Process?", w)) {
      std::system(realdata_clear);
    }
  });
  layout->addWidget(realdataclearbtn);

  layout->addStretch(1);
  return w;
}

void SettingsWindow::showEvent(QShowEvent *event) {
  panel_widget->setCurrentIndex(0);
  nav_btns->buttons()[0]->setChecked(true);
}

SettingsWindow::SettingsWindow(QWidget *parent) : QFrame(parent) {

  // setup two main layouts
  sidebar_widget = new QWidget;
  QVBoxLayout *sidebar_layout = new QVBoxLayout(sidebar_widget);
  sidebar_layout->setMargin(0);
  panel_widget = new QStackedWidget();
  panel_widget->setStyleSheet(R"(
    border-radius: 30px;
    background-color: #292929;
  )");

  // close button
  QPushButton *close_btn = new QPushButton("◀");
  close_btn->setStyleSheet(R"(
    QPushButton {
      font-size: 100px;
      padding-bottom: 20px;
      font-weight: bold;
      border 1px grey solid;
      border-radius: 100px;
      background-color: #292929;
      font-weight: 400;
    }
    QPushButton:pressed {
      background-color: #3B3B3B;
    }
  )");
  close_btn->setFixedSize(200, 200);
  sidebar_layout->addSpacing(45);
  sidebar_layout->addWidget(close_btn, 0, Qt::AlignCenter);
  QObject::connect(close_btn, &QPushButton::clicked, this, &SettingsWindow::closeSettings);

  // setup panels
  DevicePanel *device = new DevicePanel(this);
  QObject::connect(device, &DevicePanel::reviewTrainingGuide, this, &SettingsWindow::reviewTrainingGuide);
  QObject::connect(device, &DevicePanel::showDriverView, this, &SettingsWindow::showDriverView);

  QList<QPair<QString, QWidget *>> panels = {
/*
    {"Device", device},
    {"Network", network_panel(this)},
    {"Toggles", new TogglesPanel(this)},
    {"Software", new SoftwarePanel(this)},
*/
    {"Device", device},
    {"Network", network_panel(this)},
    {"Toggles", new TogglesPanel(this)},
    {"Software", new SoftwarePanel(this)},
  };

#ifdef ENABLE_MAPS
  auto map_panel = new MapPanel(this);
  panels.push_back({"Navigation", map_panel});
  QObject::connect(map_panel, &MapPanel::closeSettings, this, &SettingsWindow::closeSettings);
#endif

  const int padding = panels.size() > 3 ? 25 : 35;

  nav_btns = new QButtonGroup();
  for (auto &[name, panel] : panels) {
    QPushButton *btn = new QPushButton(name);
    btn->setCheckable(true);
    btn->setChecked(nav_btns->buttons().size() == 0);
    btn->setStyleSheet(QString(R"(
      QPushButton {
        color: grey;
        border: none;
        background: none;
        font-size: 60px;
        font-weight: 500;
        padding-top: %1px;
        padding-bottom: %1px;
      }
      QPushButton:checked {
        color: white;
      }
      QPushButton:pressed {
        color: #ADADAD;
      }
    )").arg(padding));

    nav_btns->addButton(btn);
    sidebar_layout->addWidget(btn, 0, Qt::AlignRight);

    const int lr_margin = name != "Network" ? 50 : 0;  // Network panel handles its own margins
    panel->setContentsMargins(lr_margin, 25, lr_margin, 25);

    ScrollView *panel_frame = new ScrollView(panel, this);
    panel_widget->addWidget(panel_frame);

    QObject::connect(btn, &QPushButton::clicked, [=, w = panel_frame]() {
      btn->setChecked(true);
      panel_widget->setCurrentWidget(w);
    });
  }
  sidebar_layout->setContentsMargins(50, 50, 100, 50);

  // main settings layout, sidebar + main panel
  QHBoxLayout *main_layout = new QHBoxLayout(this);

  sidebar_widget->setFixedWidth(500);
  main_layout->addWidget(sidebar_widget);
  main_layout->addWidget(panel_widget);

  setStyleSheet(R"(
    * {
      color: white;
      font-size: 50px;
    }
    SettingsWindow {
      background-color: black;
    }
  )");
}

void SettingsWindow::hideEvent(QHideEvent *event) {
#ifdef QCOM
  HardwareEon::close_activities();
#endif
}
