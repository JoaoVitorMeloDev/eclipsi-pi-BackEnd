begin;

-- Impede dois agendamentos ativos do mesmo medico no mesmo horario.
-- Consultas canceladas nao participam da exclusividade.
create unique index if not exists ux_appointments_doctor_time
    on public.consultas (medico_id, data_hora)
    where lower(status) <> 'cancelada';

commit;
