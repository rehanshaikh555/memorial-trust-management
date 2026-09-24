"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, Check, ClipboardCheck, FileBarChart, RefreshCw, Save, Users } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

import { useSchoolList, useAcademicYears, useClasses } from "@/hooks/use-academic-structure";
import {
  useAttendanceSheet,
  useBulkMarkAttendance,
  useAttendanceCorrections,
  useCreateAttendanceCorrection,
  useApproveAttendanceCorrection,
  useRejectAttendanceCorrection,
  useMonthlyAttendanceReport,
  useYearlyAttendanceReport,
  useAttendanceCalendar,
  useCreateAttendanceCalendar,
  useUpdateAttendanceCalendar,
  type AttendanceStatus,
} from "@/hooks/use-attendance";

const STATUSES: AttendanceStatus[] = ["PRESENT", "ABSENT", "LATE", "EXCUSED"];

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const [tab, setTab] = useState("daily");
  const [schoolId, setSchoolId] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [classId, setClassId] = useState("");
  const [date, setDate] = useState(today());

  const [local, setLocal] = useState<Record<string, { status: AttendanceStatus; remarks: string }>>({});
  const [correctionId, setCorrectionId] = useState("");
  const [correctionStatus, setCorrectionStatus] = useState<AttendanceStatus>("PRESENT");
  const [correctionReason, setCorrectionReason] = useState("");
  const [correctionRemarks, setCorrectionRemarks] = useState("");
  const [calendarDate, setCalendarDate] = useState(date);
  const [calendarHoliday, setCalendarHoliday] = useState("");
  const [calendarRemarks, setCalendarRemarks] = useState("");
  const [calendarWorking, setCalendarWorking] = useState(true);

  const schools = useSchoolList();
  const years = useAcademicYears();
  const classes = useClasses({
    school_id: schoolId || undefined,
    academic_year_id: academicYearId || undefined,
  });

  const sheet = useAttendanceSheet({
    school_id: schoolId || undefined,
    academic_year_id: academicYearId || undefined,
    class_id: classId || undefined,
    attendance_date: date,
  });

  const bulk = useBulkMarkAttendance();

  const records = useMemo(() => sheet.data?.items ?? [], [sheet.data]);

  useEffect(() => {
    if (!records.length) {
      // The attendance query changes asynchronously; reset the editable local sheet when it returns no records.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLocal({});
      return;
    }

    const next: Record<string, { status: AttendanceStatus; remarks: string }> = {};
    records.forEach((item) => {
      next[item.enrollment_id] = {
        status: STATUSES.includes(item.status as AttendanceStatus)
          ? (item.status as AttendanceStatus)
          : "PRESENT",
        remarks: item.remarks ?? "",
      };
    });
    // Synchronize editable attendance state with the newly loaded server sheet.
    setLocal(next);
  }, [date, classId, records]);

  const counts = useMemo(() => {
    const values = Object.values(local);
    return {
      total: values.length,
      present: values.filter((x) => x.status === "PRESENT").length,
      absent: values.filter((x) => x.status === "ABSENT").length,
      late: values.filter((x) => x.status === "LATE").length,
      excused: values.filter((x) => x.status === "EXCUSED").length,
    };
  }, [local]);

  async function saveAttendance() {
    if (!schoolId || !academicYearId || !classId || !date) {
      toast.error("Select school, academic year, class and date.");
      return;
    }

    if (!sheet.data?.is_working_day) {
      toast.error("This date is marked as a non-working day.");
      return;
    }

    await bulk.mutateAsync({
      school_id: schoolId,
      academic_year_id: academicYearId,
      class_id: classId,
      attendance_date: date,
      entries: Object.entries(local).map(([enrollment_id, value]) => ({
        enrollment_id,
        status: value.status,
        remarks: value.remarks || null,
      })),
    });

    toast.success("Attendance saved successfully.");
    await sheet.refetch();
  }

  function markAll(status: AttendanceStatus) {
    const next = { ...local };
    Object.keys(next).forEach((id) => {
      next[id] = { ...next[id], status };
    });
    setLocal(next);
    toast.success(`All students marked ${status.toLowerCase()}.`);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Attendance</h1>
          <p className="text-muted-foreground">
            Daily attendance, reports, corrections and school calendar.
          </p>
        </div>

        <Button variant="outline" onClick={() => sheet.refetch()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-4 p-4 md:grid-cols-4">
          <Select value={schoolId} onValueChange={(v) => {
            setSchoolId(v ?? "");
            setAcademicYearId("");
            setClassId("");
          }}>
            <SelectTrigger><SelectValue placeholder="School" /></SelectTrigger>
            <SelectContent>
              {(schools.data ?? []).map((school) => (
                <SelectItem key={school.id} value={school.id}>{school.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={academicYearId} onValueChange={(v) => {
            setAcademicYearId(v ?? "");
            setClassId("");
          }}>
            <SelectTrigger><SelectValue placeholder="Academic year" /></SelectTrigger>
            <SelectContent>
              {(years.data ?? []).map((year) => (
                <SelectItem key={year.id} value={year.id}>{year.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={classId} onValueChange={(v) => setClassId(v ?? "")}>
            <SelectTrigger><SelectValue placeholder="Class" /></SelectTrigger>
            <SelectContent>
              {(classes.data ?? []).map((item) => (
                <SelectItem key={item.id} value={item.id}>
                  {item.name}{item.section ? ` - ${item.section}` : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </CardContent>
      </Card>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="daily"><ClipboardCheck className="mr-2 h-4 w-4" />Daily</TabsTrigger>
          <TabsTrigger value="reports"><FileBarChart className="mr-2 h-4 w-4" />Reports</TabsTrigger>
          <TabsTrigger value="corrections"><Check className="mr-2 h-4 w-4" />Corrections</TabsTrigger>
          <TabsTrigger value="calendar"><CalendarDays className="mr-2 h-4 w-4" />Calendar</TabsTrigger>
        </TabsList>

        <TabsContent value="daily" className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {[
              ["Students", counts.total],
              ["Present", counts.present],
              ["Absent", counts.absent],
              ["Late", counts.late],
              ["Excused", counts.excused],
            ].map(([label, value]) => (
              <Card key={label}>
                <CardContent className="flex items-center justify-between p-5">
                  <div>
                    <p className="text-sm text-muted-foreground">{label}</p>
                    <p className="text-2xl font-semibold">{value}</p>
                  </div>
                  <Users className="h-5 w-5 text-muted-foreground" />
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle>Daily attendance sheet</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {sheet.data?.is_working_day ? "Working day" : "Non-working day"}
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={() => markAll("PRESENT")} disabled={!records.length}>
                  All Present
                </Button>
                <Button variant="outline" onClick={() => markAll("ABSENT")} disabled={!records.length}>
                  All Absent
                </Button>
                <Button onClick={saveAttendance} disabled={bulk.isPending || !records.length || !sheet.data?.is_working_day}>
                  <Save className="mr-2 h-4 w-4" />
                  {bulk.isPending ? "Saving..." : "Save Attendance"}
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              {!records.length ? (
                <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
                  Select a school, academic year and class to load students.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="p-3">Student</th>
                        <th className="p-3">Code</th>
                        <th className="p-3">Status</th>
                        <th className="p-3">Remarks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((student) => {
                        const value = local[student.enrollment_id];
                        return (
                          <tr key={student.enrollment_id} className="border-b">
                            <td className="p-3 font-medium">{student.student_name}</td>
                            <td className="p-3 text-muted-foreground">{student.student_code}</td>
                            <td className="p-3">
                              <Select
                                value={value?.status ?? "PRESENT"}
                                onValueChange={(v) =>
                                  setLocal((prev) => ({
                                    ...prev,
                                    [student.enrollment_id]: {
                                      ...prev[student.enrollment_id],
                                      status: v as AttendanceStatus,
                                    },
                                  }))
                                }
                                disabled={!sheet.data?.is_working_day}
                              >
                                <SelectTrigger className="w-36"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  {STATUSES.map((status) => (
                                    <SelectItem key={status} value={status}>{status}</SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="p-3">
                              <Input
                                value={value?.remarks ?? ""}
                                onChange={(e) =>
                                  setLocal((prev) => ({
                                    ...prev,
                                    [student.enrollment_id]: {
                                      ...prev[student.enrollment_id],
                                      remarks: e.target.value,
                                    },
                                  }))
                                }
                                disabled={!sheet.data?.is_working_day}
                                placeholder="Optional"
                              />
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <ReportsTab
          active={tab === "reports"}
          schoolId={schoolId}
          academicYearId={academicYearId}
          classId={classId}
          date={date}
        />

        <CorrectionsTab
          active={tab === "corrections"}
          schoolId={schoolId}
          correctionId={correctionId}
          setCorrectionId={setCorrectionId}
          correctionStatus={correctionStatus}
          setCorrectionStatus={setCorrectionStatus}
          correctionReason={correctionReason}
          setCorrectionReason={setCorrectionReason}
          correctionRemarks={correctionRemarks}
          setCorrectionRemarks={setCorrectionRemarks}
        />

        <CalendarTab
          active={tab === "calendar"}
          schoolId={schoolId}
          academicYearId={academicYearId}
          calendarDate={calendarDate}
          setCalendarDate={setCalendarDate}
          holiday={calendarHoliday}
          setHoliday={setCalendarHoliday}
          remarks={calendarRemarks}
          setRemarks={setCalendarRemarks}
          working={calendarWorking}
          setWorking={setCalendarWorking}
        />
      </Tabs>
    </div>
  );
}

function ReportsTab({ active, schoolId, academicYearId, classId, date }: {
  active: boolean;
  schoolId: string;
  academicYearId: string;
  classId: string;
  date: string;
}) {
  const [month, setMonth] = useState(date.slice(5, 7));
  const [year, setYear] = useState(date.slice(0, 4));

  const monthly = useMonthlyAttendanceReport({
    school_id: schoolId || undefined,
    academic_year_id: academicYearId || undefined,
    class_id: classId || undefined,
    month,
    year,
  });

  const yearly = useYearlyAttendanceReport({
    school_id: schoolId || undefined,
    academic_year_id: academicYearId || undefined,
  });

  if (!active) return null;

  return (
    <TabsContent value="reports" className="space-y-4">
      <Card>
        <CardContent className="flex flex-wrap gap-3 p-4">
          <Input className="w-28" value={month} onChange={(e) => setMonth(e.target.value)} placeholder="MM" />
          <Input className="w-28" value={year} onChange={(e) => setYear(e.target.value)} placeholder="YYYY" />
          <Badge variant="outline">{monthly.data?.length ?? 0} monthly rows</Badge>
          <Badge variant="outline">{yearly.data?.length ?? 0} yearly rows</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <ReportCard title="Monthly attendance" rows={monthly.data ?? []} />
        <ReportCard title="Yearly attendance" rows={yearly.data ?? []} />
      </div>
    </TabsContent>
  );
}

function ReportCard({ title, rows }: { title: string; rows: Array<{ student_name: string; attendance_percentage: number; present_days: number; absent_days: number; late_days: number }> }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        {!rows.length ? (
          <p className="text-sm text-muted-foreground">No report data available.</p>
        ) : (
          <div className="space-y-3">
            {rows.slice(0, 10).map((row, index) => (
              <div key={`${row.student_name}-${index}`} className="flex items-center justify-between border-b pb-3">
                <div>
                  <p className="font-medium">{row.student_name}</p>
                  <p className="text-xs text-muted-foreground">
                    P {row.present_days} · A {row.absent_days} · L {row.late_days}
                  </p>
                </div>
                <Badge>{Number(row.attendance_percentage).toFixed(1)}%</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CorrectionsTab({
  active, schoolId, correctionId, setCorrectionId, correctionStatus,
  setCorrectionStatus, correctionReason, setCorrectionReason,
  correctionRemarks, setCorrectionRemarks,
}: {
  active: boolean;
  schoolId: string;
  correctionId: string;
  setCorrectionId: (v: string) => void;
  correctionStatus: AttendanceStatus;
  setCorrectionStatus: (v: AttendanceStatus) => void;
  correctionReason: string;
  setCorrectionReason: (v: string) => void;
  correctionRemarks: string;
  setCorrectionRemarks: (v: string) => void;
}) {
  const corrections = useAttendanceCorrections({ school_id: schoolId || undefined });
  const create = useCreateAttendanceCorrection();
  const approve = useApproveAttendanceCorrection();
  const reject = useRejectAttendanceCorrection();

  if (!active) return null;

  async function submit() {
    if (!correctionId || !correctionReason.trim()) {
      toast.error("Select an attendance record ID and enter a reason.");
      return;
    }

    await create.mutateAsync({
      attendance_id: correctionId,
      requested_status: correctionStatus,
      requested_remarks: correctionRemarks || null,
      reason: correctionReason,
    });

    setCorrectionId("");
    setCorrectionReason("");
    setCorrectionRemarks("");
    toast.success("Correction request submitted.");
  }

  return (
    <TabsContent value="corrections" className="space-y-4">
      <Card>
        <CardHeader><CardTitle>Request attendance correction</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-4">
          <Input value={correctionId} onChange={(e) => setCorrectionId(e.target.value)} placeholder="Attendance record ID" />
          <Select value={correctionStatus} onValueChange={(v) => setCorrectionStatus(v as AttendanceStatus)}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{STATUSES.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
          </Select>
          <Input value={correctionReason} onChange={(e) => setCorrectionReason(e.target.value)} placeholder="Reason" />
          <Button onClick={submit} disabled={create.isPending}>Submit correction</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Correction requests</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          {(corrections.data ?? []).map((item) => (
            <div key={item.id} className="flex flex-col gap-3 rounded-lg border p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-medium">{item.attendance_date} · {item.old_status} → {item.requested_status}</p>
                <p className="text-sm text-muted-foreground">{item.reason}</p>
                <Badge variant="outline" className="mt-2">{item.status}</Badge>
              </div>
              {item.status === "PENDING" && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => approve.mutate({ correctionId: item.id, payload: {} })}>Approve</Button>
                  <Button size="sm" variant="outline" onClick={() => reject.mutate({ correctionId: item.id, payload: {} })}>Reject</Button>
                </div>
              )}
            </div>
          ))}
          {!corrections.data?.length && <p className="text-sm text-muted-foreground">No correction requests.</p>}
        </CardContent>
      </Card>
    </TabsContent>
  );
}

function CalendarTab({
  active, schoolId, academicYearId, calendarDate, setCalendarDate,
  holiday, setHoliday, remarks, setRemarks, working, setWorking,
}: {
  active: boolean;
  schoolId: string;
  academicYearId: string;
  calendarDate: string;
  setCalendarDate: (v: string) => void;
  holiday: string;
  setHoliday: (v: string) => void;
  remarks: string;
  setRemarks: (v: string) => void;
  working: boolean;
  setWorking: (v: boolean) => void;
}) {
  const calendar = useAttendanceCalendar({
    school_id: schoolId || undefined,
    academic_year_id: academicYearId || undefined,
  });
  const create = useCreateAttendanceCalendar();
  const update = useUpdateAttendanceCalendar();

  if (!active) return null;

  async function save() {
    if (!schoolId || !academicYearId || !calendarDate) {
      toast.error("Select school, academic year and date.");
      return;
    }

    const existing = (calendar.data ?? []).find((item) => item.calendar_date === calendarDate);

    if (existing) {
      await update.mutateAsync({
        calendarId: existing.id,
        payload: {
          is_working_day: working,
          holiday_name: holiday || null,
          remarks: remarks || null,
        },
      });
    } else {
      await create.mutateAsync({
        school_id: schoolId,
        academic_year_id: academicYearId,
        calendar_date: calendarDate,
        is_working_day: working,
        day_type: working ? "REGULAR" : "HOLIDAY",
        holiday_name: holiday || null,
        remarks: remarks || null,
      });
    }

    toast.success("Calendar updated.");
    await calendar.refetch();
  }

  return (
    <TabsContent value="calendar" className="space-y-4">
      <Card>
        <CardHeader><CardTitle>School calendar</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-5">
          <Input type="date" value={calendarDate} onChange={(e) => setCalendarDate(e.target.value)} />
          <Input value={holiday} onChange={(e) => setHoliday(e.target.value)} placeholder="Holiday name" />
          <Textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} placeholder="Remarks" />
          <Select value={working ? "WORKING" : "HOLIDAY"} onValueChange={(v) => setWorking(v === "WORKING")}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="WORKING">Working day</SelectItem>
              <SelectItem value="HOLIDAY">Non-working day</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={save} disabled={create.isPending || update.isPending}>Save calendar</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Calendar entries</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {(calendar.data ?? []).slice(0, 30).map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-lg border p-3">
              <div>
                <p className="font-medium">{item.calendar_date}</p>
                <p className="text-sm text-muted-foreground">{item.holiday_name || item.day_type}</p>
              </div>
              <Badge variant={item.is_working_day ? "default" : "secondary"}>
                {item.is_working_day ? "Working" : "Holiday"}
              </Badge>
            </div>
          ))}
        </CardContent>
      </Card>
    </TabsContent>
  );
}
