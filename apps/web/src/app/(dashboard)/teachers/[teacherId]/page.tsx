"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import {
  ArrowLeft,
  BriefcaseBusiness,
  CheckCircle2,
  GraduationCap,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Save,
  Send,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";

import {
  useApproveTeacher,
  useDeactivateTeacher,
  useTeacher,
  useTeacherAssignments,
  useTeacherAttendance,
  useUpdateTeacher,
  useReadyTeacher,
  useSubmitTeacher,
} from "@/hooks/use-teachers";
import { useSchool } from "@/hooks/use-academic-structure";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function statusClass(status: string) {
  switch (status) {
    case "ACTIVE":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";
    case "SUBMITTED":
      return "border-blue-200 bg-blue-50 text-blue-700";
    case "READY_FOR_APPROVAL":
      return "border-violet-200 bg-violet-50 text-violet-700";
    case "APPLICATION_DRAFT":
      return "border-amber-200 bg-amber-50 text-amber-700";
    case "INACTIVE":
    case "DEACTIVATED":
      return "border-slate-200 bg-slate-100 text-slate-600";
    default:
      return "border-slate-200 bg-slate-50 text-slate-600";
  }
}

function ActionButton({
  label,
  icon: Icon,
  loading,
  disabled,
  onClick,
  variant = "default",
}: {
  label: string;
  icon: typeof Send;
  loading: boolean;
  disabled?: boolean;
  onClick: () => void;
  variant?: "default" | "danger";
}) {
  return (
    <Button
      type="button"
      disabled={disabled || loading}
      onClick={onClick}
      className={
        variant === "danger"
          ? "rounded-xl bg-red-600 hover:bg-red-700"
          : "rounded-xl bg-[#27348B] hover:bg-[#202c78]"
      }
    >
      {loading ? (
        <Loader2 className="mr-2 size-4 animate-spin" />
      ) : (
        <Icon className="mr-2 size-4" />
      )}
      {label}
    </Button>
  );
}

export default function TeacherDetailPage() {
  const params = useParams<{ teacherId: string }>();
  const teacherId = params.teacherId;

  const teacher = useTeacher(teacherId);
  const update = useUpdateTeacher(teacherId);
  const submit = useSubmitTeacher(teacherId);
  const ready = useReadyTeacher(teacherId);
  const approve = useApproveTeacher(teacherId);
  const deactivate = useDeactivateTeacher(teacherId);

  const [editing, setEditing] = useState(false);

  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [gender, setGender] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [qualification, setQualification] = useState("");

  const record = teacher.data;

  const school = useSchool(record?.school_id);
  const assignments = useTeacherAssignments({
    teacherId,
    schoolId: record?.school_id,
    includeInactive: true,
  });
  const attendance = useTeacherAttendance({
    teacherId,
    schoolId: record?.school_id,
  });

  const fullName = useMemo(
    () =>
      record
        ? [
            record.first_name,
            record.middle_name,
            record.last_name,
          ]
            .filter(Boolean)
            .join(" ")
        : "",
    [record],
  );

  const startEditing = () => {
    if (!record) return;

    setFirstName(record.first_name);
    setMiddleName(record.middle_name ?? "");
    setLastName(record.last_name ?? "");
    setDateOfBirth(record.date_of_birth ?? "");
    setGender(record.gender ?? "");
    setPhone(record.phone ?? "");
    setEmail(record.email ?? "");
    setAddress(record.address ?? "");
    setQualification(record.qualification ?? "");
    setEditing(true);
  };

  const saveChanges = async () => {
    await update.mutateAsync({
      first_name: firstName.trim(),
      middle_name: middleName.trim() || null,
      last_name: lastName.trim() || null,
      date_of_birth: dateOfBirth || null,
      gender: gender || null,
      phone: phone.trim() || null,
      email: email.trim() || null,
      address: address.trim() || null,
      qualification: qualification.trim() || null,
    });

    setEditing(false);
  };

  if (teacher.isLoading) {
    return (
      <div className="flex min-h-[500px] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-[#27348B]" />
      </div>
    );
  }

  if (teacher.isError || !record) {
    return (
      <div className="mx-auto max-w-4xl rounded-3xl border border-red-100 bg-red-50 p-10 text-center">
        <XCircle className="mx-auto size-10 text-red-500" />
        <h1 className="mt-4 text-xl font-bold text-red-800">
          Teacher could not be loaded
        </h1>
        <p className="mt-2 text-sm text-red-600">
          {teacher.error instanceof Error
            ? teacher.error.message
            : "The teacher API request failed."}
        </p>
        <Link
          href="/teachers"
          className="mt-6 inline-flex rounded-xl bg-[#27348B] px-4 py-2.5 text-sm font-bold text-white"
        >
          Back to teachers
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1500px]">
      <div className="mb-6">
        <Link
          href="/teachers"
          className="inline-flex items-center gap-2 text-xs font-bold text-[#27348B]"
        >
          <ArrowLeft className="size-4" />
          Back to teachers
        </Link>
      </div>

      <Card className="overflow-hidden border-white/50 bg-white/70 shadow-xl shadow-[#27348B]/10 backdrop-blur-xl">
        <div className="bg-[#27348B] p-6 text-white sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex size-16 shrink-0 items-center justify-center rounded-2xl bg-white/15 text-2xl font-black ring-1 ring-white/20">
                {record.first_name.charAt(0).toUpperCase()}
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.15em] text-white/55">
                  Teacher profile
                </p>
                <h1 className="mt-1 text-2xl font-black">
                  {fullName}
                </h1>
                <p className="mt-1 text-xs text-white/60">
                  Teacher ID: {record.teacher_id}
                </p>
              </div>
            </div>

            <Badge
              variant="outline"
              className={`w-fit rounded-full ${statusClass(record.status)}`}
            >
              {record.status}
            </Badge>
          </div>
        </div>

        <CardContent className="p-6">
          <div className="flex flex-wrap gap-2">
            {record.status === "APPLICATION_DRAFT" && (
              <ActionButton
                label="Submit application"
                icon={Send}
                loading={submit.isPending}
                onClick={() => submit.mutate()}
              />
            )}

            {record.status === "SUBMITTED" && (
              <ActionButton
                label="Ready for approval"
                icon={CheckCircle2}
                loading={ready.isPending}
                onClick={() => ready.mutate()}
              />
            )}

            {record.status === "READY_FOR_APPROVAL" && (
              <ActionButton
                label="Approve teacher"
                icon={CheckCircle2}
                loading={approve.isPending}
                onClick={() => approve.mutate()}
              />
            )}

            {record.status === "ACTIVE" && (
              <ActionButton
                label="Deactivate"
                icon={XCircle}
                loading={deactivate.isPending}
                onClick={() => {
                  if (
                    window.confirm(
                      "Deactivate this teacher?",
                    )
                  ) {
                    deactivate.mutate();
                  }
                }}
                variant="danger"
              />
            )}

            <Link
              href={`/teachers/${teacherId}/assignments`}
              className="inline-flex h-10 items-center justify-center rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:border-[#27348B]/30 hover:text-[#27348B]"
            >
              <BriefcaseBusiness className="mr-2 size-4" />
              Manage assignments
            </Link>

            {!editing && record.status !== "DEACTIVATED" && (
              <Button
                type="button"
                variant="outline"
                className="rounded-xl"
                onClick={startEditing}
              >
                Edit profile
              </Button>
            )}
          </div>

          {update.isError && (
            <div className="mt-4 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">
              {update.error instanceof Error
                ? update.error.message
                : "Unable to update teacher."}
            </div>
          )}
        </CardContent>
      </Card>

      {editing && (
        <Card className="mt-6 border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <UserRound className="size-4 text-[#27348B]" />
              Edit teacher information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  First name
                </label>
                <Input
                  value={firstName}
                  onChange={(event) =>
                    setFirstName(event.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Middle name
                </label>
                <Input
                  value={middleName}
                  onChange={(event) =>
                    setMiddleName(event.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Last name
                </label>
                <Input
                  value={lastName}
                  onChange={(event) =>
                    setLastName(event.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Date of birth
                </label>
                <Input
                  type="date"
                  value={dateOfBirth}
                  onChange={(event) =>
                    setDateOfBirth(event.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Gender
                </label>
                <Select
                  value={gender}
                  onValueChange={(value) =>
                    setGender(value ?? "")
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MALE">
                      Male
                    </SelectItem>
                    <SelectItem value="FEMALE">
                      Female
                    </SelectItem>
                    <SelectItem value="OTHER">
                      Other
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Qualification
                </label>
                <Input
                  value={qualification}
                  onChange={(event) =>
                    setQualification(event.target.value)
                  }
                  placeholder="B.Ed, M.Ed..."
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Phone
                </label>
                <Input
                  value={phone}
                  onChange={(event) =>
                    setPhone(event.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500">
                  Email
                </label>
                <Input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-500">
                Address
              </label>
              <Textarea
                rows={3}
                value={address}
                onChange={(event) =>
                  setAddress(event.target.value)
                }
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                className="rounded-xl"
                onClick={() => setEditing(false)}
              >
                Cancel
              </Button>

              <Button
                type="button"
                disabled={
                  update.isPending ||
                  !firstName.trim()
                }
                className="rounded-xl bg-[#27348B] hover:bg-[#202c78]"
                onClick={saveChanges}
              >
                {update.isPending ? (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                ) : (
                  <Save className="mr-2 size-4" />
                )}
                Save changes
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <UserRound className="size-4 text-[#27348B]" />
              Personal information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {[
              ["Date of birth", record.date_of_birth],
              ["Gender", record.gender],
              ["Qualification", record.qualification],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {label}
                </p>
                <p className="mt-1 text-sm font-medium text-slate-700">
                  {value || "Not provided"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Phone className="size-4 text-[#27348B]" />
              Contact information
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Phone
              </p>
              <p className="mt-1 flex items-center gap-2 text-sm font-medium text-slate-700">
                <Phone className="size-3.5 text-slate-400" />
                {record.phone || "Not provided"}
              </p>
            </div>

            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Email
              </p>
              <p className="mt-1 flex items-center gap-2 break-all text-sm font-medium text-slate-700">
                <Mail className="size-3.5 text-slate-400" />
                {record.email || "Not provided"}
              </p>
            </div>

            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Address
              </p>
              <p className="mt-1 flex gap-2 text-sm font-medium text-slate-700">
                <MapPin className="mt-0.5 size-3.5 shrink-0 text-slate-400" />
                {record.address || "Not provided"}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <GraduationCap className="size-4 text-[#27348B]" />
              School
            </CardTitle>
          </CardHeader>

          <CardContent>
            {school.isLoading ? (
              <p className="text-sm text-slate-400">
                Loading school...
              </p>
            ) : school.data ? (
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    School name
                  </p>
                  <p className="mt-1 font-semibold text-slate-800">
                    {school.data.name}
                  </p>
                </div>

                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    School code
                  </p>
                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {school.data.code}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400">
                School information unavailable.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <BriefcaseBusiness className="size-4 text-[#27348B]" />
              Assignments
            </CardTitle>
          </CardHeader>

          <CardContent>
            {assignments.isLoading ? (
              <p className="text-sm text-slate-400">
                Loading assignments...
              </p>
            ) : assignments.data?.length ? (
              <div className="space-y-3">
                {assignments.data.map((assignment) => (
                  <div
                    key={assignment.id}
                    className="rounded-2xl border border-slate-100 bg-white/70 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-800">
                          {assignment.subject ||
                            "General assignment"}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          Class:{" "}
                          {assignment.class_id ||
                            "Not assigned"}
                        </p>
                      </div>

                      <Badge
                        variant="outline"
                        className="rounded-full"
                      >
                        {assignment.status}
                      </Badge>
                    </div>

                    <p className="mt-3 text-xs text-slate-500">
                      {assignment.start_date}
                      {assignment.end_date
                        ? ` → ${assignment.end_date}`
                        : " → Current"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                <p className="text-sm font-medium text-slate-600">
                  No assignments recorded
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/50 bg-white/70 shadow-xl backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Users className="size-4 text-[#27348B]" />
              Attendance
            </CardTitle>
          </CardHeader>

          <CardContent>
            {attendance.isLoading ? (
              <p className="text-sm text-slate-400">
                Loading attendance...
              </p>
            ) : attendance.data?.length ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl bg-[#27348B]/5 p-5">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Records
                  </p>
                  <p className="mt-1 text-2xl font-black text-[#27348B]">
                    {attendance.data.length}
                  </p>
                </div>

                <div className="rounded-2xl bg-emerald-50 p-5">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Present
                  </p>
                  <p className="mt-1 text-2xl font-black text-emerald-700">
                    {
                      attendance.data.filter(
                        (item) =>
                          item.status === "PRESENT",
                      ).length
                    }
                  </p>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center">
                <p className="text-sm font-medium text-slate-600">
                  No attendance records found
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
